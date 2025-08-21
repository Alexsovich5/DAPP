#!/usr/bin/env python3
"""
Model Relationship Validation Script
Validates foreign key constraints and relationship integrity across all models
"""

import sys
import logging
from sqlalchemy import create_engine, inspect, MetaData, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def validate_database_relationships():
    """Validate foreign key constraints and relationships in the database"""
    
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/dinner_app")
    
    try:
        # Create engine and connect
        engine = create_engine(database_url)
        inspector = inspect(engine)
        
        logger.info("🔍 Validating database relationships and foreign key constraints...")
        
        # Get all tables
        tables = inspector.get_table_names()
        logger.info(f"Found {len(tables)} tables: {', '.join(tables)}")
        
        # Track foreign key relationships
        foreign_keys = {}
        relationship_issues = []
        
        for table_name in tables:
            # Get foreign keys for each table
            fks = inspector.get_foreign_keys(table_name)
            
            if fks:
                foreign_keys[table_name] = fks
                logger.info(f"Table '{table_name}' has {len(fks)} foreign key constraints")
                
                for fk in fks:
                    logger.info(f"  ↳ {fk['constrained_columns']} → {fk['referred_table']}.{fk['referred_columns']}")
        
        # Validate specific critical relationships
        critical_relationships = [
            # Core relationships
            ("profiles", "users", "user_id"),
            ("matches", "users", "sender_id"),
            ("matches", "users", "receiver_id"),
            ("messages", "soul_connections", "connection_id"),
            ("messages", "users", "sender_id"),
            ("daily_revelations", "soul_connections", "connection_id"),
            ("daily_revelations", "users", "sender_id"),
            ("soul_connections", "users", "user1_id"),
            ("soul_connections", "users", "user2_id"),
            ("soul_connections", "users", "initiated_by"),
            
            # Safety relationships
            ("user_reports", "users", "reporter_id"),
            ("user_reports", "users", "reported_user_id"),
            ("blocked_users", "users", "blocker_id"),
            ("blocked_users", "users", "blocked_user_id"),
            ("user_safety_profiles", "users", "user_id"),
            
            # Photo reveal relationships
            ("user_photos", "users", "user_id"),
            ("photo_reveal_timelines", "soul_connections", "connection_id"),
            ("photo_reveal_requests", "photo_reveal_timelines", "timeline_id"),
            ("photo_reveal_requests", "user_photos", "photo_id"),
            ("photo_reveal_permissions", "user_photos", "photo_id"),
            ("photo_reveal_permissions", "soul_connections", "connection_id"),
        ]
        
        logger.info("\n🔗 Validating critical foreign key relationships...")
        
        missing_relationships = []
        for child_table, parent_table, column in critical_relationships:
            if child_table in tables and parent_table in tables:
                # Check if foreign key exists
                fks = foreign_keys.get(child_table, [])
                fk_exists = any(
                    column in fk['constrained_columns'] and 
                    parent_table == fk['referred_table']
                    for fk in fks
                )
                
                if fk_exists:
                    logger.info(f"✅ {child_table}.{column} → {parent_table} (FK exists)")
                else:
                    logger.warning(f"❌ {child_table}.{column} → {parent_table} (FK missing)")
                    missing_relationships.append((child_table, parent_table, column))
            else:
                logger.warning(f"⚠️  Table missing: {child_table} or {parent_table}")
        
        # Validate indexes for foreign key columns
        logger.info("\n📊 Validating indexes on foreign key columns...")
        
        missing_indexes = []
        for table_name in tables:
            if table_name in foreign_keys:
                indexes = inspector.get_indexes(table_name)
                index_columns = set()
                for idx in indexes:
                    index_columns.update(idx['column_names'])
                
                for fk in foreign_keys[table_name]:
                    for col in fk['constrained_columns']:
                        if col not in index_columns:
                            logger.warning(f"❌ Missing index on {table_name}.{col}")
                            missing_indexes.append((table_name, col))
                        else:
                            logger.info(f"✅ Index exists on {table_name}.{col}")
        
        # Check for circular dependencies or problematic relationships
        logger.info("\n🔄 Checking for potential circular dependencies...")
        
        dependency_graph = {}
        for table_name, fks in foreign_keys.items():
            dependency_graph[table_name] = []
            for fk in fks:
                dependency_graph[table_name].append(fk['referred_table'])
        
        # Simple cycle detection
        def has_cycle(graph, start, visited=None, rec_stack=None):
            if visited is None:
                visited = set()
            if rec_stack is None:
                rec_stack = set()
            
            visited.add(start)
            rec_stack.add(start)
            
            for neighbor in graph.get(start, []):
                if neighbor not in visited:
                    if has_cycle(graph, neighbor, visited, rec_stack):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(start)
            return False
        
        cycles_detected = []
        for table in dependency_graph:
            if has_cycle(dependency_graph, table):
                cycles_detected.append(table)
        
        if cycles_detected:
            logger.warning(f"⚠️  Potential circular dependencies detected in: {cycles_detected}")
        else:
            logger.info("✅ No circular dependencies detected")
        
        # Test basic referential integrity with sample queries
        logger.info("\n🧪 Testing referential integrity with sample queries...")
        
        with engine.connect() as conn:
            # Test orphaned records
            integrity_tests = [
                ("profiles", "user_id", "users", "id"),
                ("messages", "sender_id", "users", "id"),
                ("messages", "connection_id", "soul_connections", "id"),
                ("daily_revelations", "sender_id", "users", "id"),
                ("daily_revelations", "connection_id", "soul_connections", "id"),
            ]
            
            orphaned_records = []
            for child_table, child_col, parent_table, parent_col in integrity_tests:
                if child_table in tables and parent_table in tables:
                    try:
                        result = conn.execute(text(f"""
                            SELECT COUNT(*) as orphaned_count
                            FROM {child_table} c
                            LEFT JOIN {parent_table} p ON c.{child_col} = p.{parent_col}
                            WHERE p.{parent_col} IS NULL AND c.{child_col} IS NOT NULL
                        """))
                        
                        orphaned_count = result.scalar()
                        if orphaned_count > 0:
                            logger.warning(f"❌ {orphaned_count} orphaned records in {child_table}.{child_col}")
                            orphaned_records.append((child_table, child_col, orphaned_count))
                        else:
                            logger.info(f"✅ No orphaned records in {child_table}.{child_col}")
                            
                    except Exception as e:
                        logger.warning(f"⚠️  Could not test {child_table}.{child_col}: {str(e)}")
        
        # Generate summary report
        logger.info("\n📋 VALIDATION SUMMARY")
        logger.info("=" * 50)
        
        if missing_relationships:
            logger.info(f"❌ Missing Foreign Key Constraints: {len(missing_relationships)}")
            for child, parent, col in missing_relationships:
                logger.info(f"   • {child}.{col} → {parent}")
        else:
            logger.info("✅ All critical foreign key constraints are present")
        
        if missing_indexes:
            logger.info(f"❌ Missing Indexes on FK Columns: {len(missing_indexes)}")
            for table, col in missing_indexes:
                logger.info(f"   • {table}.{col}")
        else:
            logger.info("✅ All foreign key columns have indexes")
        
        if orphaned_records:
            logger.info(f"❌ Orphaned Records Found: {len(orphaned_records)}")
            for table, col, count in orphaned_records:
                logger.info(f"   • {table}.{col}: {count} records")
        else:
            logger.info("✅ No orphaned records detected")
        
        if cycles_detected:
            logger.info(f"⚠️  Circular Dependencies: {len(cycles_detected)} tables")
        else:
            logger.info("✅ No circular dependencies")
        
        # Overall assessment
        total_issues = len(missing_relationships) + len(missing_indexes) + len(orphaned_records)
        
        if total_issues == 0:
            logger.info("\n🎉 DATABASE RELATIONSHIPS: EXCELLENT")
            logger.info("All foreign key constraints, indexes, and referential integrity checks passed!")
            return True
        else:
            logger.info(f"\n⚠️  DATABASE RELATIONSHIPS: {total_issues} ISSUES FOUND")
            logger.info("Review the issues above and apply the necessary migrations.")
            return False
            
    except Exception as e:
        logger.error(f"❌ Validation failed: {str(e)}")
        return False


def validate_model_imports():
    """Validate that all models can be imported and initialized"""
    logger.info("\n🐍 Validating model imports and SQLAlchemy setup...")
    
    try:
        # Import all models to ensure they're properly defined
        from app.models.user import User
        from app.models.profile import Profile
        from app.models.match import Match
        from app.models.message import Message
        from app.models.daily_revelation import DailyRevelation
        from app.models.soul_connection import SoulConnection
        from app.models.photo_reveal import (
            UserPhoto, PhotoRevealTimeline, PhotoRevealRequest, 
            PhotoRevealPermission, PhotoRevealEvent, PhotoModerationLog
        )
        from app.models.user_safety import (
            UserReport, BlockedUser, UserSafetyProfile, ModerationAction
        )
        
        logger.info("✅ All models imported successfully")
        
        # Check that relationships are properly defined
        model_relationships = {
            'User': ['profile', 'sent_matches', 'received_matches', 'photos'],
            'Profile': ['user'],
            'Match': ['sender', 'receiver'],
            'Message': ['connection', 'sender'],
            'DailyRevelation': ['connection', 'sender'],
            'SoulConnection': ['user1', 'user2', 'revelations', 'messages'],
        }
        
        models = {
            'User': User,
            'Profile': Profile,
            'Match': Match,
            'Message': Message,
            'DailyRevelation': DailyRevelation,
            'SoulConnection': SoulConnection,
        }
        
        for model_name, expected_relationships in model_relationships.items():
            model_class = models[model_name]
            for rel_name in expected_relationships:
                if hasattr(model_class, rel_name):
                    logger.info(f"✅ {model_name}.{rel_name} relationship exists")
                else:
                    logger.warning(f"❌ {model_name}.{rel_name} relationship missing")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Model import failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Model validation failed: {str(e)}")
        return False


if __name__ == "__main__":
    logger.info("🚀 Starting Database Relationship Validation")
    logger.info("=" * 60)
    
    # Validate model imports first
    models_valid = validate_model_imports()
    
    # Then validate database relationships
    db_valid = validate_database_relationships()
    
    # Overall result
    if models_valid and db_valid:
        logger.info("\n🎉 ALL VALIDATIONS PASSED!")
        logger.info("Database relationships and model definitions are properly configured.")
        sys.exit(0)
    else:
        logger.info("\n❌ VALIDATION FAILED!")
        logger.info("Please review and fix the issues identified above.")
        sys.exit(1)