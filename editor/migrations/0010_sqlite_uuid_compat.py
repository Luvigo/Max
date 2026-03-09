# Migración para compatibilidad UUID en SQLite.
# La migración 0003 solo convierte Institution/Membership a UUID en PostgreSQL.
# Esta migración aplica la conversión equivalente en SQLite para que los tests funcionen.

import uuid
from django.db import connection, migrations


def _convert_sqlite_uuid(apps, schema_editor):
    """Convierte Institution y Membership de integer a UUID en SQLite."""
    if connection.vendor != 'sqlite':
        return
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(editor_institution)")
        cols = cursor.fetchall()
        id_col = next((c for c in cols if c[1] == 'id'), None)
        col_type = (id_col[2] or '').lower()
        need_inst = id_col and not any(t in col_type for t in ('char', 'varchar', 'text'))
        inst_map = {}
        if need_inst:
            cursor.execute("SELECT * FROM editor_institution")
            inst_rows = cursor.fetchall()
            col_names = [c[1] for c in cols]
            id_idx = col_names.index('id')
            new_inst_rows = []
            for row in inst_rows:
                old_id = row[id_idx]
                new_id = str(uuid.uuid4())
                inst_map[old_id] = new_id
                new_row = list(row)
                new_row[id_idx] = new_id
                new_inst_rows.append(tuple(new_row))
            cursor.execute("""
                CREATE TABLE editor_institution_new (
                    id TEXT NOT NULL PRIMARY KEY,
                    name varchar(200) NOT NULL,
                    code varchar(50) NOT NULL UNIQUE,
                    description text NOT NULL,
                    created_at datetime NOT NULL,
                    updated_at datetime NOT NULL,
                    is_active bool NOT NULL,
                    logo varchar(200) NOT NULL,
                    slug varchar(100) NOT NULL UNIQUE,
                    status varchar(20) NOT NULL,
                    agent_token varchar(64) NULL,
                    address varchar(300) NOT NULL,
                    city varchar(100) NOT NULL,
                    country varchar(100) NOT NULL,
                    email varchar(254) NOT NULL,
                    phone varchar(30) NOT NULL,
                    postal_code varchar(20) NOT NULL,
                    state varchar(100) NOT NULL,
                    website varchar(200) NOT NULL
                )
            """)
            for row in new_inst_rows:
                ph = ','.join(['?' for _ in row])
                cursor.execute("INSERT INTO editor_institution_new VALUES (" + ph + ")", row)
            cursor.execute("DROP TABLE editor_institution")
            cursor.execute("ALTER TABLE editor_institution_new RENAME TO editor_institution")

        cursor.execute("PRAGMA table_info(editor_membership)")
        mcols = cursor.fetchall()
        mid_col = next((c for c in mcols if c[1] == 'id'), None)
        mcol_type = (mid_col[2] or '').lower() if mid_col else ''
        if mid_col and ('integer' in mcol_type or 'bigint' in mcol_type):
            cursor.execute("SELECT * FROM editor_membership")
            mrows = cursor.fetchall()
            mcol_names = [c[1] for c in mcols]
            mid_idx = mcol_names.index('id')
            iid_idx = mcol_names.index('institution_id')
            new_mrows = []
            for row in mrows:
                new_row = list(row)
                new_row[mid_idx] = str(uuid.uuid4())
                old_iid = row[iid_idx]
                new_row[iid_idx] = inst_map.get(old_iid, str(uuid.uuid4()))
                new_mrows.append(tuple(new_row))
            cursor.execute("""
                CREATE TABLE editor_membership_new (
                    id TEXT NOT NULL PRIMARY KEY,
                    role varchar(20) NOT NULL,
                    is_active bool NOT NULL,
                    created_at datetime NOT NULL,
                    updated_at datetime NOT NULL,
                    notes text NOT NULL,
                    institution_id TEXT NOT NULL,
                    user_id integer NOT NULL
                )
            """)
            for row in new_mrows:
                ph = ','.join(['?' for _ in row])
                cursor.execute("INSERT INTO editor_membership_new VALUES (" + ph + ")", row)
            cursor.execute("DROP TABLE editor_membership")
            cursor.execute("ALTER TABLE editor_membership_new RENAME TO editor_membership")


def _noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [('editor', '0009_add_notification_model')]
    operations = [migrations.RunPython(_convert_sqlite_uuid, _noop_reverse)]
