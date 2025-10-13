#!/usr/bin/env python3
"""
Script to fix migration file b3300a3ef02f by wrapping all ALTER operations
in conditional checks for table existence.
"""

# Read the migration file
migration_file = "python-backend/alembic/versions/b3300a3ef02f_add_user_activity_tracking_models_with_.py"

with open(migration_file, "r") as f:
    content = f.read()

# Tables that were dropped in earlier migrations and need conditional ALTER operations
affected_tables = [
    "behavioral_patterns",
    "compatibility_predictions",
    "ml_models",
    "model_predictions",
    "personalized_recommendations",
    "user_profiles",
]

# Find the section after "existing_tables = inspector.get_table_names()"
# and before the first affected table operation

# Split content into lines
lines = content.split("\n")

# Find where we need to start wrapping operations
output_lines = []
in_alter_section = False
current_table = None
indent_level = 0

for i, line in enumerate(lines):
    # Track when we reach the existing_tables section
    if "existing_tables = inspector.get_table_names()" in line:
        output_lines.append(line)
        in_alter_section = True
        continue

    # If we're in the alter section and hit a table operation
    if in_alter_section:
        # Check if this line starts operations on an affected table
        for table in affected_tables:
            if f'"{table}"' in line and any(
                op in line
                for op in [
                    "op.add_column",
                    "op.alter_column",
                    "op.drop_column",
                    "op.create_foreign_key",
                    "op.drop_constraint",
                ]
            ):
                # Start a conditional block if we're not already in one for this table
                if current_table != table:
                    # Close previous conditional block if exists
                    if current_table:
                        output_lines.append("")

                    # Start new conditional block
                    output_lines.append(
                        f"    # Conditional ALTER operations for {table} (may have been dropped by earlier migrations)"
                    )
                    output_lines.append(f'    if "{table}" in existing_tables:')
                    current_table = table
                    indent_level = 8  # 2 levels of indentation (4 spaces each)

                # Add the operation line with extra indentation
                output_lines.append(" " * indent_level + line.strip())
                continue

        # Check if we've moved to a different section (end of ALTER operations)
        if "op.add_column" in line and '"users"' in line:
            # Close the last conditional block
            if current_table:
                output_lines.append("")
                current_table = None
                in_alter_section = False
            output_lines.append(line)
            continue

    # Default: just add the line as-is
    output_lines.append(line)

# Write the fixed migration file
with open(migration_file, "w") as f:
    f.write("\n".join(output_lines))

print(f"✓ Fixed migration file: {migration_file}")
print(f"✓ Wrapped ALTER operations for tables: {', '.join(affected_tables)}")
