"""
Tests for AGY Advanced Schema (P3.10, P3.11, P3.12, P3.13)
"""
import json
import os
import sys
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)

from living_objects import EventStore, CapabilityRegistry
from prototypes.agy.p1_enhanced.agy_living_object import TieredReasoningEngine
from prototypes.agy.p1_enhanced.agy_advanced_schema import (
    AdvancedSchemaFactory,
    EnhancedObjectSchema,
    PropertyDef,
    MethodDef,
    RelationshipDef,
    SchemaMigration,
    SchemaMigrator,
    SchemaRegistry,
)


@pytest.fixture
def runtime(tmp_path):
    store = EventStore(str(tmp_path / "schema_test.db"))
    registry = CapabilityRegistry()
    engine = TieredReasoningEngine()
    yield store, registry, engine


def test_schema_to_yaml_and_back():
    """P3.10: Verify YAML serialization and deserialization round-trip."""
    schema = EnhancedObjectSchema(
        type_name="smart_meter",
        version="1.2.0",
        description="Electricity metering living object",
        properties=[
            PropertyDef(name="kwh_reading", type="float", default=0.0, min_value=0.0),
            PropertyDef(name="status", type="enum", allowed_values=["active", "suspended"], default="active"),
        ],
        relationships=[
            RelationshipDef(name="grid_substation", target_type="substation", cardinality="many-to-one"),
        ],
        goals=["accurately_measure_usage", "report_peak_demand"],
        tags=["energy", "meter"],
        methods=[
            MethodDef(name="diagnose_meter_drift", return_type="dict", description="Diagnose drift", intelligent=True),
        ],
    )

    yaml_text = schema.to_yaml()
    assert "type_name: smart_meter" in yaml_text
    assert "version: 1.2.0" in yaml_text
    assert "kwh_reading" in yaml_text

    reloaded = EnhancedObjectSchema.from_yaml(yaml_text)
    assert reloaded.type_name == "smart_meter"
    assert reloaded.version == "1.2.0"
    assert len(reloaded.properties) == 2
    assert len(reloaded.relationships) == 1
    assert reloaded.relationships[0].name == "grid_substation"
    assert len(reloaded.goals) == 2
    assert len(reloaded.methods) == 1


def test_schema_registry():
    """P3.11: Test central schema registry and version catalog."""
    registry = SchemaRegistry()
    s1 = EnhancedObjectSchema(
        type_name="turbine",
        version="1.0.0",
        description="Wind turbine",
        properties=[PropertyDef(name="rpm", type="float", default=0.0)],
    )
    s2 = EnhancedObjectSchema(
        type_name="turbine",
        version="2.0.0",
        description="Wind turbine v2 with blade pitch",
        properties=[
            PropertyDef(name="rpm", type="float", default=0.0),
            PropertyDef(name="pitch_angle", type="float", default=45.0),
        ],
    )

    registry.register(s1)
    registry.register(s2)

    assert registry.list_types() == ["turbine"]
    assert registry.list_versions("turbine") == ["1.0.0", "2.0.0"]
    assert registry.get("turbine").version == "2.0.0"
    assert registry.get("turbine", "1.0.0").version == "1.0.0"


def test_schema_migration(runtime):
    """P3.12: Test migrating stored object state from v1 to v2 schema."""
    store, registry, engine = runtime
    factory = AdvancedSchemaFactory()

    v1_schema = EnhancedObjectSchema(
        type_name="pump",
        version="1.0.0",
        description="Pump v1",
        properties=[
            PropertyDef(name="flow_rate", type="float", default=10.0),
            PropertyDef(name="old_metric", type="string", default="legacy_val"),
        ],
    )
    v2_schema = EnhancedObjectSchema(
        type_name="pump",
        version="2.0.0",
        description="Pump v2 with pressure and renamed metric",
        properties=[
            PropertyDef(name="flow_rate", type="float", default=10.0),
            PropertyDef(name="new_metric", type="string", default="standard_val"),
            PropertyDef(name="pressure_psi", type="float", default=50.0),
        ],
    )

    PumpV1Class = factory.create_class(v1_schema)
    pump = PumpV1Class.create(store, registry, engine, name="Pump_101", initial_state={"flow_rate": 15.5, "old_metric": "custom_data"})
    pump.save()
    p_id = pump.object_id

    # Register migration rule: rename old_metric -> new_metric, add pressure_psi default
    migrator = SchemaMigrator(store)
    migrator.register_migration(SchemaMigration(
        type_name="pump",
        from_version="1.0.0",
        to_version="2.0.0",
        renamed_fields={"old_metric": "new_metric"},
        default_additions={"pressure_psi": 50.0},
    ))

    success = migrator.migrate_object(p_id, target_schema=v2_schema, from_version="1.0.0")
    assert success is True

    # Reload under v2 class
    PumpV2Class = factory.create_class(v2_schema)
    pump_v2 = PumpV2Class.load(p_id, store, registry, engine)
    assert pump_v2.get_state("flow_rate") == 15.5
    assert pump_v2.get_state("new_metric") == "custom_data"
    assert pump_v2.get_state("pressure_psi") == 50.0

    # Verify migration event was appended to audit trail
    events = store.get_events(p_id, event_type="schema_migration")
    assert len(events) == 1
    payload = json.loads(events[0].payload) if isinstance(events[0].payload, str) else events[0].payload
    assert payload["to_version"] == "2.0.0"


def test_relationships_in_generated_class(runtime):
    """P3.13: Test relationship methods in schema-generated classes."""
    store, registry, engine = runtime
    factory = AdvancedSchemaFactory()

    cluster_schema = EnhancedObjectSchema(
        type_name="server_cluster",
        version="1.0.0",
        description="Cluster containing server nodes",
        properties=[PropertyDef(name="cluster_name", type="string", default="Cluster-A")],
        relationships=[
            RelationshipDef(name="nodes", target_type="server_node", cardinality="one-to-many"),
            RelationshipDef(name="primary_datacenter", target_type="datacenter", cardinality="many-to-one"),
        ],
    )

    ClusterClass = factory.create_class(cluster_schema)
    cluster = ClusterClass.create(store, registry, engine, name="ProdCluster")

    # Test one-to-many relationship helper
    cluster.add_nodes("node-uuid-1")
    cluster.add_nodes("node-uuid-2")
    assert cluster.get_nodes() == ["node-uuid-1", "node-uuid-2"]

    # Test many-to-one relationship helper
    cluster.set_primary_datacenter("dc-us-east")
    assert cluster.get_primary_datacenter() == "dc-us-east"

    cluster.save()
    loaded = ClusterClass.load(cluster.object_id, store, registry, engine)
    assert loaded.get_nodes() == ["node-uuid-1", "node-uuid-2"]
    assert loaded.get_primary_datacenter() == "dc-us-east"
