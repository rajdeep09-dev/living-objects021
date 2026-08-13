"""
AGY Advanced Schema Module — P3 Phase 3 Completion
===================================================

Implements the remaining P3 features:
  - P3.10: Schema-to-YAML & YAML-to-Schema Round-Trip
  - P3.11: Central SchemaRegistry with versioning and directory loading
  - P3.12: Schema Migration Engine (v1 -> v2 state upgrades with event logging)
  - P3.13: Relationship Schemas (one-to-one, one-to-many, many-to-one, peer refs)
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from living_objects import CapabilityRegistry, EventStore
from prototypes.agy.p1_enhanced.agy_living_object import AGYLivingObject, TieredReasoningEngine
from prototypes.agy.p1_enhanced.agy_schema_factory import (
    MethodDef,
    ObjectSchema,
    PropertyDef,
    RETURN_MAP,
    SCHEMA_TYPES,
    SchemaValidationError,
    SchemaValidator,
)


# ---------------------------------------------------------------------------
# P3.13: RelationshipDef
# ---------------------------------------------------------------------------

@dataclass
class RelationshipDef:
    """Defines a relationship between Living Objects."""
    name: str
    target_type: str
    cardinality: str = "many-to-one"  # "one-to-one", "one-to-many", "many-to-one", "peer"
    description: str = ""
    cascade_retire: bool = False


# ---------------------------------------------------------------------------
# Enhanced ObjectSchema with Version & Relationships
# ---------------------------------------------------------------------------

@dataclass
class EnhancedObjectSchema(ObjectSchema):
    version: str = "1.0.0"
    relationships: List[RelationshipDef] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "type_name": self.type_name,
            "version": self.version,
            "description": self.description,
            "properties": [asdict(p) for p in self.properties],
            "goals": list(self.goals),
            "constraints": dict(self.constraints),
            "methods": [asdict(m) for m in self.methods],
            "tags": list(self.tags),
            "relationships": [asdict(r) for r in self.relationships],
        }

    @classmethod
    def from_dict(cls, data: dict) -> EnhancedObjectSchema:
        props = [
            PropertyDef(
                name=p["name"],
                type=p["type"],
                description=p.get("description", ""),
                default=p.get("default"),
                required=p.get("required", True),
                allowed_values=p.get("allowed_values"),
                min_value=p.get("min_value"),
                max_value=p.get("max_value"),
            )
            for p in data.get("properties", [])
        ]
        methods = [
            MethodDef(
                name=m["name"],
                return_type=m.get("return_type", "string"),
                description=m.get("description", ""),
                intelligent=m.get("intelligent", True),
                implementation=m.get("implementation"),
            )
            for m in data.get("methods", [])
        ]
        relationships = [
            RelationshipDef(
                name=r["name"],
                target_type=r["target_type"],
                cardinality=r.get("cardinality", "many-to-one"),
                description=r.get("description", ""),
                cascade_retire=r.get("cascade_retire", False),
            )
            for r in data.get("relationships", [])
        ]
        return cls(
            type_name=data["type_name"],
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            properties=props,
            goals=data.get("goals", []),
            constraints=data.get("constraints", {}),
            methods=methods,
            tags=data.get("tags", []),
            relationships=relationships,
        )

    # -----------------------------------------------------------------------
    # P3.10: YAML Serialization & Deserialization
    # -----------------------------------------------------------------------

    def to_yaml(self) -> str:
        """Serialize schema to clean YAML format."""
        d = self.to_dict()
        lines = [
            f"type_name: {d['type_name']}",
            f"version: {d['version']}",
            f"description: \"{d['description']}\"",
            "properties:",
        ]
        for p in d["properties"]:
            lines.append(f"  - name: {p['name']}")
            lines.append(f"    type: {p['type']}")
            if p["description"]:
                lines.append(f"    description: \"{p['description']}\"")
            if p["default"] is not None:
                lines.append(f"    default: {json.dumps(p['default'])}")
            if p.get("allowed_values"):
                lines.append(f"    allowed_values: {json.dumps(p['allowed_values'])}")
            if p.get("min_value") is not None:
                lines.append(f"    min_value: {p['min_value']}")
            if p.get("max_value") is not None:
                lines.append(f"    max_value: {p['max_value']}")

        if d.get("relationships"):
            lines.append("relationships:")
            for r in d["relationships"]:
                lines.append(f"  - name: {r['name']}")
                lines.append(f"    target_type: {r['target_type']}")
                lines.append(f"    cardinality: {r['cardinality']}")
                if r["description"]:
                    lines.append(f"    description: \"{r['description']}\"")

        if d.get("goals"):
            lines.append("goals:")
            for g in d["goals"]:
                lines.append(f"  - \"{g}\"")

        if d.get("tags"):
            lines.append("tags:")
            for t in d["tags"]:
                lines.append(f"  - {t}")

        if d.get("constraints"):
            lines.append("constraints:")
            for k, v in d["constraints"].items():
                lines.append(f"  {k}: {json.dumps(v)}")

        if d.get("methods"):
            lines.append("methods:")
            for m in d["methods"]:
                lines.append(f"  - name: {m['name']}")
                lines.append(f"    return_type: {m['return_type']}")
                lines.append(f"    description: \"{m['description']}\"")
                lines.append(f"    intelligent: {str(m['intelligent']).lower()}")
                if m.get("implementation"):
                    lines.append(f"    implementation: {json.dumps(m['implementation'])}")

        return "\n".join(lines) + "\n"

    @classmethod
    def from_yaml(cls, yaml_str: str) -> EnhancedObjectSchema:
        """
        Robust YAML parser for ObjectSchema without third-party dependencies.
        Parses YAML schema structure accurately.
        """
        # Fallback to json if json format is provided
        stripped = yaml_str.strip()
        if stripped.startswith("{") and stripped.endswith("}"):
            return cls.from_dict(json.loads(stripped))

        # Lightweight standard YAML parser
        data: Dict[str, Any] = {
            "properties": [],
            "methods": [],
            "relationships": [],
            "goals": [],
            "tags": [],
            "constraints": {},
        }
        current_section = None
        current_item: Optional[dict] = None

        for line in yaml_str.splitlines():
            trimmed = line.strip()
            if not trimmed or trimmed.startswith("#"):
                continue

            # Top-level keys
            top_match = re.match(r"^([a-zA-Z0-9_]+):\s*(.*)$", line)
            if top_match and not line.startswith(" ") and not line.startswith("\t"):
                key, val = top_match.group(1), top_match.group(2).strip()
                current_section = key
                current_item = None
                if val:
                    val_unquoted = val.strip('"\'')
                    if val.startswith("[") and val.endswith("]"):
                        try:
                            data[key] = json.loads(val)
                        except json.JSONDecodeError:
                            data[key] = [x.strip() for x in val[1:-1].split(",") if x.strip()]
                    else:
                        data[key] = val_unquoted
                continue

            # Nested sections
            if current_section in ("properties", "methods", "relationships"):
                item_start = re.match(r"^\s*-\s+([a-zA-Z0-9_]+):\s*(.*)$", line)
                if item_start:
                    k, v = item_start.group(1), item_start.group(2).strip().strip('"\'')
                    if v.startswith("[") or v.startswith("{"):
                        try:
                            v = json.loads(v)
                        except json.JSONDecodeError:
                            pass
                    current_item = {k: v}
                    data[current_section].append(current_item)
                elif current_item is not None:
                    field_match = re.match(r"^\s+([a-zA-Z0-9_]+):\s*(.*)$", line)
                    if field_match:
                        k, v = field_match.group(1), field_match.group(2).strip()
                        v_clean = v.strip('"\'')
                        if v.lower() == "true":
                            current_item[k] = True
                        elif v.lower() == "false":
                            current_item[k] = False
                        elif v.isdigit():
                            current_item[k] = int(v)
                        elif re.match(r"^-?\d+(\.\d+)?$", v):
                            current_item[k] = float(v)
                        elif v.startswith("[") or v.startswith("{"):
                            try:
                                current_item[k] = json.loads(v)
                            except json.JSONDecodeError:
                                current_item[k] = v_clean
                        else:
                            current_item[k] = v_clean

            elif current_section in ("goals", "tags"):
                list_item = re.match(r"^\s*-\s+[\"']?(.*?)[\"']?$", line)
                if list_item:
                    data[current_section].append(list_item.group(1).strip())

            elif current_section == "constraints":
                constraint_match = re.match(r"^\s+([a-zA-Z0-9_]+):\s*(.*)$", line)
                if constraint_match:
                    k, v = constraint_match.group(1), constraint_match.group(2).strip()
                    try:
                        data["constraints"][k] = json.loads(v)
                    except json.JSONDecodeError:
                        data["constraints"][k] = v

        return cls.from_dict(data)


# ---------------------------------------------------------------------------
# P3.11: Schema Registry
# ---------------------------------------------------------------------------

class SchemaRegistry:
    """
    Central repository for Living Object schemas.
    Supports versioning, schema retrieval, export, and dynamic loading.
    """
    def __init__(self):
        self._schemas: Dict[str, Dict[str, EnhancedObjectSchema]] = {}  # type_name -> version -> schema
        self._latest_version: Dict[str, str] = {}                       # type_name -> latest_version

    def register(self, schema: EnhancedObjectSchema) -> None:
        """Register an object schema."""
        errors = SchemaValidator().validate(schema)
        if errors:
            raise SchemaValidationError(f"Cannot register invalid schema '{schema.type_name}': {errors}")
        t = schema.type_name
        v = schema.version
        if t not in self._schemas:
            self._schemas[t] = {}
        self._schemas[t][v] = schema
        self._latest_version[t] = v

    def get(self, type_name: str, version: Optional[str] = None) -> Optional[EnhancedObjectSchema]:
        """Get schema by type name and optional version."""
        if type_name not in self._schemas:
            return None
        if version is None:
            version = self._latest_version.get(type_name)
        return self._schemas[type_name].get(version)

    def list_types(self) -> List[str]:
        """List all registered type names."""
        return sorted(list(self._schemas.keys()))

    def list_versions(self, type_name: str) -> List[str]:
        """List all registered versions for a type."""
        return sorted(list(self._schemas.get(type_name, {}).keys()))

    def export_catalog(self) -> Dict[str, Any]:
        """Export all registered schemas as a dictionary catalog."""
        catalog = {}
        for t, versions in self._schemas.items():
            catalog[t] = {v: s.to_dict() for v, s in versions.items()}
        return catalog

    def load_from_directory(self, dir_path: str) -> int:
        """Load schemas from YAML/JSON files in a directory."""
        if not os.path.exists(dir_path):
            return 0
        loaded = 0
        for fname in os.listdir(dir_path):
            if fname.endswith((".yaml", ".yml", ".json")):
                full_path = os.path.join(dir_path, fname)
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                try:
                    schema = EnhancedObjectSchema.from_yaml(content)
                    self.register(schema)
                    loaded += 1
                except Exception:
                    pass
        return loaded


# ---------------------------------------------------------------------------
# P3.12: Schema Versioning & State Migration Engine
# ---------------------------------------------------------------------------

class SchemaMigration:
    """
    Defines transformation rules to migrate an object's state from v_from to v_to.
    """
    def __init__(
        self,
        type_name: str,
        from_version: str,
        to_version: str,
        renamed_fields: Optional[Dict[str, str]] = None,
        default_additions: Optional[Dict[str, Any]] = None,
        custom_transform: Optional[Callable[[dict], dict]] = None,
    ):
        self.type_name = type_name
        self.from_version = from_version
        self.to_version = to_version
        self.renamed_fields = renamed_fields or {}
        self.default_additions = default_additions or {}
        self.custom_transform = custom_transform

    def apply(self, state: dict) -> dict:
        """Apply migrations to state dictionary."""
        new_state = dict(state)

        # 1. Renamed fields
        for old_k, new_k in self.renamed_fields.items():
            if old_k in new_state:
                new_state[new_k] = new_state.pop(old_k)

        # 2. Add defaults for new fields
        for k, default_val in self.default_additions.items():
            if k not in new_state:
                new_state[k] = default_val

        # 3. Custom transform
        if self.custom_transform:
            new_state = self.custom_transform(new_state)

        return new_state


class SchemaMigrator:
    """
    Applies SchemaMigrations to stored Living Objects in EventStore.
    """
    def __init__(self, store: EventStore):
        self.store = store
        self._migrations: Dict[Tuple[str, str, str], SchemaMigration] = {}

    def register_migration(self, migration: SchemaMigration) -> None:
        key = (migration.type_name, migration.from_version, migration.to_version)
        self._migrations[key] = migration

    def migrate_object(
        self,
        object_id: str,
        target_schema: EnhancedObjectSchema,
        from_version: str = "1.0.0",
    ) -> bool:
        """Migrate a specific object in the SQLite event store to target schema version."""
        row = self.store.get_object(object_id)
        if not row:
            return False

        current_state = json.loads(row["current_state"])
        key = (target_schema.type_name, from_version, target_schema.version)
        migration = self._migrations.get(key)

        if migration:
            migrated_state = migration.apply(current_state)
        else:
            # Automatic migration: supply defaults for missing target properties
            migrated_state = dict(current_state)
            for p in target_schema.properties:
                if p.name not in migrated_state:
                    migrated_state[p.name] = (
                        p.default if p.default is not None
                        else SCHEMA_TYPES.get(p.type, {}).get("default")
                    )

        # Update in EventStore
        version = row["state_version"] + 1
        self.store.update_state(object_id, migrated_state, version)

        # Record migration event in audit trail
        self.store.append_event(
            EventStore.__module__ and __import__("living_objects.core.event_store", fromlist=["Event"]).Event(
                event_id=str(__import__("uuid").uuid4()),
                object_id=object_id,
                timestamp=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
                event_type="schema_migration",
                payload={
                    "from_version": from_version,
                    "to_version": target_schema.version,
                    "type_name": target_schema.type_name,
                },
                parent_event_id=None,
            )
        )
        return True


# ---------------------------------------------------------------------------
# Enhanced Schema Factory with Relationship Methods
# ---------------------------------------------------------------------------

class AdvancedSchemaFactory:
    """
    Factory creating AGYLivingObjects with full relationship navigation,
    YAML import/export, and schema registry integration.
    """
    def __init__(self, registry: Optional[SchemaRegistry] = None):
        self.registry = registry or SchemaRegistry()
        self._cache: Dict[Tuple[str, str], Type[AGYLivingObject]] = {}

    def create_class(self, schema: EnhancedObjectSchema) -> Type[AGYLivingObject]:
        errors = SchemaValidator().validate(schema)
        if errors:
            raise SchemaValidationError(f"Invalid schema '{schema.type_name}': {errors}")

        cache_key = (schema.type_name, schema.version)
        if cache_key in self._cache:
            return self._cache[cache_key]

        cls_name = "".join(w.capitalize() for w in schema.type_name.split("_"))
        class_dict = self._build_class_dict(schema)

        cls = type(cls_name, (AGYLivingObject,), class_dict)
        cls.__doc__ = (
            f"Schema {schema.type_name} (v{schema.version})\n"
            f"{schema.description}\n"
            f"Goals: {', '.join(schema.goals)}"
        )

        # Wrap intelligent methods
        for attr_name, method in list(class_dict.items()):
            if callable(method) and getattr(method, "_schema_intelligent", False):
                def _wrap(orig):
                    def wrapper(self, *args, **kwargs):
                        return self._execute_intelligent(orig, *args, **kwargs)
                    wrapper.__name__ = orig.__name__
                    wrapper.__doc__ = orig.__doc__
                    wrapper._agy_intelligent = True
                    return wrapper
                setattr(cls, attr_name, _wrap(method))

        self.registry.register(schema)
        self._cache[cache_key] = cls
        return cls

    def _build_class_dict(self, schema: EnhancedObjectSchema) -> dict:
        d: dict = {"_schema": schema}

        # default_initial_state
        def _default_state(cls_self) -> dict:
            state = {}
            for p in cls_self._schema.properties:
                if p.default is not None:
                    state[p.name] = p.default
                elif p.type == "list":
                    state[p.name] = []
                elif p.type == "dict":
                    state[p.name] = {}
                else:
                    state[p.name] = SCHEMA_TYPES.get(p.type, {}).get("default")
            # Default relationships
            for r in getattr(cls_self._schema, "relationships", []):
                if r.cardinality in ("one-to-many", "peer"):
                    state[r.name] = []
                else:
                    state[r.name] = None
            return state
        d["default_initial_state"] = classmethod(_default_state)

        # create / load
        def _create(cls_self, store, registry, reasoning, object_id=None,
                    name=None, initial_state=None, tags=None, goals=None):
            init = cls_self.default_initial_state()
            if initial_state:
                init.update(initial_state)
            obj = AGYLivingObject.create(
                store=store, registry=registry, reasoning=reasoning,
                object_id=object_id,
                name=name or cls_self._schema.type_name,
                initial_state=init,
                tags=tags or cls_self._schema.tags,
                goals=goals or cls_self._schema.goals,
            )
            obj.__class__ = cls_self
            obj.expected_state = dict(init)
            return obj
        d["create"] = classmethod(_create)

        def _load(cls_self, object_id, store, registry, reasoning):
            obj = AGYLivingObject.load(object_id, store, registry, reasoning)
            if obj:
                obj.__class__ = cls_self
            return obj
        d["load"] = classmethod(_load)

        # Property accessors
        for prop in schema.properties:
            pname = prop.name
            pdefault = prop.default

            def make_getter(pn, pd):
                def getter(self) -> Any:
                    return self.get_state(pn, pd)
                getter.__name__ = f"get_{pn}"
                return getter

            def make_setter(pn):
                def setter(self, value: Any) -> None:
                    self.set_state(pn, value)
                setter.__name__ = f"set_{pn}"
                return setter

            d[f"get_{pname}"] = make_getter(pname, pdefault)
            d[f"set_{pname}"] = make_setter(pname)

        # P3.13: Relationship methods
        for rel in schema.relationships:
            rname = rel.name
            rcard = rel.cardinality

            if rcard in ("one-to-many", "peer"):
                def make_rel_adder(rn):
                    def add_rel(self, target_id: str) -> None:
                        current = self.get_state(rn, []) or []
                        if target_id not in current:
                            current.append(target_id)
                            self.set_state(rn, current)
                    add_rel.__name__ = f"add_{rn}"
                    return add_rel

                def make_rel_getter(rn):
                    def get_rel(self) -> List[str]:
                        return self.get_state(rn, []) or []
                    get_rel.__name__ = f"get_{rn}"
                    return get_rel

                d[f"add_{rname}"] = make_rel_adder(rname)
                d[f"get_{rname}"] = make_rel_getter(rname)
            else:
                def make_single_rel_setter(rn):
                    def set_rel(self, target_id: Optional[str]) -> None:
                        self.set_state(rn, target_id)
                    set_rel.__name__ = f"set_{rn}"
                    return set_rel

                def make_single_rel_getter(rn):
                    def get_rel(self) -> Optional[str]:
                        return self.get_state(rn, None)
                    get_rel.__name__ = f"get_{rn}"
                    return get_rel

                d[f"set_{rname}"] = make_single_rel_setter(rname)
                d[f"get_{rname}"] = make_single_rel_getter(rname)

        # Methods
        for mdef in schema.methods:
            if mdef.intelligent:
                rtype = RETURN_MAP.get(mdef.return_type, str)
                def make_intelligent(m):
                    def intelligent(self, *args, **kwargs) -> rtype:
                        return self._execute_intelligent(intelligent, *args, **kwargs)
                    intelligent.__name__ = m.name
                    intelligent.__doc__ = m.description
                    intelligent._schema_intelligent = True
                    return intelligent
                d[mdef.name] = make_intelligent(mdef)
            else:
                code = mdef.implementation or "return None"
                globs = {"json": json, "__import__": __import__}
                exec(f"def {mdef.name}(self, *args, **kwargs):\n" + textwrap.indent(code, "    "), globs)
                fn = globs[mdef.name]
                fn.__doc__ = mdef.description
                d[mdef.name] = fn

        return d
