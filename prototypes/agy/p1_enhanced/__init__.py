"""AGY prototype — Full Lifecycle, Ecology, Economics & Advanced Schema Living Objects Runtime."""
from prototypes.agy.p1_enhanced.agy_living_object import (
    AGYLivingObject,
    AnomalyRecord,
    IntelligenceScheduler,
    TieredReasoningEngine,
    ObjectDiscoveryRegistry,
)
from prototypes.agy.p1_enhanced.agy_schema_factory import (
    AGYSchemaFactory,
    SchemaValidator,
    SchemaValidationError,
    ObjectSchema,
    PropertyDef,
    MethodDef,
    CUSTOMER_SCHEMA,
    ORDER_SCHEMA,
    SUPPORT_AGENT_SCHEMA,
)
from prototypes.agy.p1_enhanced.agnes_reasoning_engine import (
    AgnesReasoningEngine,
    TieredAgnesEngine,
)
from prototypes.agy.p1_enhanced.agy_advanced_schema import (
    AdvancedSchemaFactory,
    EnhancedObjectSchema,
    RelationshipDef,
    SchemaMigration,
    SchemaMigrator,
    SchemaRegistry,
)
from prototypes.agy.p1_enhanced.agy_ecology_economics import (
    ConsensusEngine,
    ConsensusProposal,
    DelegationEngine,
    GlobalResourcePool,
    Goal,
    GoalDirectedMixin,
    ObjectSpawner,
    PopulationManager,
    ResourceBid,
    UtilityPriorityScheduler,
)

__all__ = [
    # Core AGY
    "AGYLivingObject",
    "AnomalyRecord",
    "IntelligenceScheduler",
    "TieredReasoningEngine",
    "ObjectDiscoveryRegistry",
    # Reasoning
    "AgnesReasoningEngine",
    "TieredAgnesEngine",
    # Schema Factory
    "AGYSchemaFactory",
    "SchemaValidator",
    "SchemaValidationError",
    "ObjectSchema",
    "PropertyDef",
    "MethodDef",
    "CUSTOMER_SCHEMA",
    "ORDER_SCHEMA",
    "SUPPORT_AGENT_SCHEMA",
    # Advanced Schema
    "AdvancedSchemaFactory",
    "EnhancedObjectSchema",
    "RelationshipDef",
    "SchemaMigration",
    "SchemaMigrator",
    "SchemaRegistry",
    # Ecology & Economics
    "Goal",
    "GoalDirectedMixin",
    "DelegationEngine",
    "ConsensusEngine",
    "ConsensusProposal",
    "ObjectSpawner",
    "PopulationManager",
    "GlobalResourcePool",
    "ResourceBid",
    "UtilityPriorityScheduler",
]
