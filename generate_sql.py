import os
import importlib
import inspect
import re
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Date, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base

# Path to our models
models_dir = "app/domain/models"
models_package = "app.domain.models"

def get_model_files():
    """Get all Python files in the models directory."""
    model_files = []
    for file in os.listdir(models_dir):
        if file.endswith(".py") and file != "__init__.py":
            model_files.append(file)
    return model_files

def import_model_from_file(file_name):
    """Import a model from a file."""
    module_name = f"{models_package}.{file_name[:-3]}"
    try:
        module = importlib.import_module(module_name)
        # Find all classes that are SQLAlchemy models
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and hasattr(obj, "__tablename__"):
                return obj
    except ImportError as e:
        print(f"Failed to import {module_name}: {e}")
    return None

def get_column_type_sql(column):
    """Convert SQLAlchemy column type to PostgreSQL type."""
    if isinstance(column.type, String):
        length = getattr(column.type, "length", None)
        return f"VARCHAR({length})" if length else "TEXT"
    elif isinstance(column.type, Integer):
        return "INTEGER"
    elif isinstance(column.type, Float):
        return "FLOAT"
    elif isinstance(column.type, Boolean):
        return "BOOLEAN"
    elif isinstance(column.type, DateTime):
        return "TIMESTAMP WITH TIME ZONE"
    elif isinstance(column.type, Date):
        return "DATE"
    elif isinstance(column.type, Text):
        return "TEXT"
    elif isinstance(column.type, JSON):
        return "JSONB"
    else:
        return "TEXT"  # Default fallback

def generate_create_table_sql(model):
    """Generate CREATE TABLE SQL for a model."""
    if not hasattr(model, "__tablename__"):
        return None
    
    table_name = model.__tablename__
    sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
    
    columns = []
    primary_keys = []
    foreign_keys = []
    
    for name, column in model.__dict__.items():
        if not isinstance(column, Column):
            continue
            
        column_def = f"    {name} {get_column_type_sql(column)}"
        
        if column.primary_key:
            primary_keys.append(name)
            column_def += " PRIMARY KEY"
            
        if column.nullable is False and not column.primary_key:
            column_def += " NOT NULL"
            
        if column.unique:
            column_def += " UNIQUE"
            
        if column.server_default is not None:
            # Extract the default value expression
            default_value = str(column.server_default)
            if "func.now()" in default_value:
                column_def += " DEFAULT CURRENT_TIMESTAMP"
            else:
                # Try to extract the default value
                match = re.search(r"text\('(.+)'\)", default_value)
                if match:
                    column_def += f" DEFAULT '{match.group(1)}'"
                    
        if isinstance(column.type, ForeignKey):
            fk_table, fk_column = str(column.type.target_fullname).split(".")
            foreign_keys.append(f"    FOREIGN KEY ({name}) REFERENCES {fk_table}({fk_column})")
            
        columns.append(column_def)
    
    sql += ",\n".join(columns)
    
    if foreign_keys:
        sql += ",\n" + ",\n".join(foreign_keys)
    
    sql += "\n);\n"
    
    # Add indexes
    indexes = []
    for name, column in model.__dict__.items():
        if isinstance(column, Column) and column.index and not column.primary_key:
            indexes.append(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_{name} ON {table_name} ({name});")
    
    if indexes:
        sql += "\n" + "\n".join(indexes) + "\n"
        
    return sql

def manually_create_sql():
    """Create SQL schema manually based on examining the model files."""
    sql = """-- PostgreSQL Database Schema for Exam Management System
-- Generated from SQLAlchemy models

BEGIN;

-- Enable uuid-ossp extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables with proper dependencies order

-- Role table
CREATE TABLE IF NOT EXISTS roles (
    role_id VARCHAR(50) PRIMARY KEY,
    role_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Permission table
CREATE TABLE IF NOT EXISTS permissions (
    permission_id VARCHAR(50) PRIMARY KEY,
    permission_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Role Permission mapping
CREATE TABLE IF NOT EXISTS role_permissions (
    id VARCHAR(50) PRIMARY KEY,
    role_id VARCHAR(50) NOT NULL,
    permission_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(permission_id) ON DELETE CASCADE,
    UNIQUE (role_id, permission_id)
);

-- User table
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(50) PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'admin',
    role_id VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    require_2fa BOOLEAN DEFAULT FALSE,
    two_factor_secret VARCHAR(100),
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    backup_codes TEXT,
    last_login TIMESTAMP WITH TIME ZONE,
    last_login_ip VARCHAR(45),
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

-- Two Factor Backup Codes
CREATE TABLE IF NOT EXISTS two_factor_backup (
    id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    backup_code VARCHAR(100) NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Security Log
CREATE TABLE IF NOT EXISTS security_logs (
    log_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50),
    action VARCHAR(50) NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Invitation
CREATE TABLE IF NOT EXISTS invitation (
    invitation_id VARCHAR(50) PRIMARY KEY,
    email VARCHAR(100) NOT NULL,
    token VARCHAR(100) NOT NULL UNIQUE,
    role_id VARCHAR(50),
    created_by VARCHAR(50),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Management Unit
CREATE TABLE IF NOT EXISTS management_unit (
    unit_id VARCHAR(50) PRIMARY KEY,
    unit_name VARCHAR(200) NOT NULL,
    unit_type VARCHAR(50) NOT NULL,
    address TEXT,
    contact_info JSONB,
    parent_unit_id VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (parent_unit_id) REFERENCES management_unit(unit_id) ON DELETE SET NULL
);

-- Exam Type
CREATE TABLE IF NOT EXISTS exam_type (
    type_id VARCHAR(50) PRIMARY KEY,
    type_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Exam
CREATE TABLE IF NOT EXISTS exam (
    exam_id VARCHAR(50) PRIMARY KEY,
    exam_name VARCHAR(200) NOT NULL,
    type_id VARCHAR(50) NOT NULL,
    start_date DATE,
    end_date DATE,
    scope VARCHAR(50),
    organizing_unit_id VARCHAR(50),
    additional_info TEXT,
    exam_metadata JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (type_id) REFERENCES exam_type(type_id),
    FOREIGN KEY (organizing_unit_id) REFERENCES management_unit(unit_id)
);

-- Exam Location
CREATE TABLE IF NOT EXISTS exam_location (
    location_id VARCHAR(50) PRIMARY KEY,
    location_name VARCHAR(200) NOT NULL,
    address TEXT NOT NULL,
    capacity INTEGER,
    contact_person VARCHAR(100),
    contact_phone VARCHAR(20),
    contact_email VARCHAR(100),
    coordinates JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Exam Location Mapping
CREATE TABLE IF NOT EXISTS exam_location_mapping (
    mapping_id VARCHAR(50) PRIMARY KEY,
    exam_id VARCHAR(50) NOT NULL,
    location_id VARCHAR(50) NOT NULL,
    capacity INTEGER,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (exam_id) REFERENCES exam(exam_id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES exam_location(location_id) ON DELETE CASCADE,
    UNIQUE (exam_id, location_id)
);

-- Exam Room
CREATE TABLE IF NOT EXISTS exam_room (
    room_id VARCHAR(50) PRIMARY KEY,
    room_name VARCHAR(100) NOT NULL,
    location_id VARCHAR(50) NOT NULL,
    capacity INTEGER NOT NULL,
    floor VARCHAR(20),
    building VARCHAR(100),
    room_type VARCHAR(50),
    equipment JSONB,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (location_id) REFERENCES exam_location(location_id) ON DELETE CASCADE
);

-- Subject
CREATE TABLE IF NOT EXISTS subject (
    subject_id VARCHAR(50) PRIMARY KEY,
    subject_code VARCHAR(20) NOT NULL UNIQUE,
    subject_name VARCHAR(100) NOT NULL,
    description TEXT,
    subject_type VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Exam Subject
CREATE TABLE IF NOT EXISTS exam_subject (
    exam_subject_id VARCHAR(50) PRIMARY KEY,
    exam_id VARCHAR(50) NOT NULL,
    subject_id VARCHAR(50) NOT NULL,
    max_score FLOAT NOT NULL,
    passing_score FLOAT,
    weight FLOAT DEFAULT 1.0,
    is_required BOOLEAN DEFAULT TRUE,
    exam_format VARCHAR(50),
    duration INTEGER,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (exam_id) REFERENCES exam(exam_id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subject(subject_id) ON DELETE CASCADE,
    UNIQUE (exam_id, subject_id)
);

-- Exam Schedule
CREATE TABLE IF NOT EXISTS exam_schedule (
    schedule_id VARCHAR(50) PRIMARY KEY,
    exam_id VARCHAR(50) NOT NULL,
    exam_subject_id VARCHAR(50) NOT NULL,
    location_id VARCHAR(50) NOT NULL,
    room_id VARCHAR(50),
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    supervisor_info JSONB,
    status VARCHAR(20) DEFAULT 'scheduled',
    capacity INTEGER,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (exam_id) REFERENCES exam(exam_id) ON DELETE CASCADE,
    FOREIGN KEY (exam_subject_id) REFERENCES exam_subject(exam_subject_id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES exam_location(location_id) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES exam_room(room_id) ON DELETE SET NULL
);

-- Candidate
CREATE TABLE IF NOT EXISTS candidate (
    candidate_id VARCHAR(20) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Personal Info
CREATE TABLE IF NOT EXISTS personal_info (
    info_id VARCHAR(50) PRIMARY KEY,
    candidate_id VARCHAR(20) NOT NULL UNIQUE,
    date_of_birth DATE,
    gender VARCHAR(10),
    id_number VARCHAR(20) UNIQUE,
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (candidate_id) REFERENCES candidate(candidate_id) ON DELETE CASCADE
);

-- Education Level
CREATE TABLE IF NOT EXISTS education_level (
    level_id VARCHAR(50) PRIMARY KEY,
    level_name VARCHAR(100) NOT NULL,
    level_code VARCHAR(20) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- School
CREATE TABLE IF NOT EXISTS school (
    school_id VARCHAR(50) PRIMARY KEY,
    school_name VARCHAR(200) NOT NULL,
    school_code VARCHAR(20) UNIQUE,
    address TEXT,
    school_type VARCHAR(50),
    contact_info JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Major
CREATE TABLE IF NOT EXISTS major (
    major_id VARCHAR(50) PRIMARY KEY,
    major_name VARCHAR(100) NOT NULL,
    major_code VARCHAR(20) UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- School Major mapping
CREATE TABLE IF NOT EXISTS school_major (
    id VARCHAR(50) PRIMARY KEY,
    school_id VARCHAR(50) NOT NULL,
    major_id VARCHAR(50) NOT NULL,
    available_seats INTEGER,
    requirements JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (school_id) REFERENCES school(school_id) ON DELETE CASCADE,
    FOREIGN KEY (major_id) REFERENCES major(major_id) ON DELETE CASCADE,
    UNIQUE (school_id, major_id)
);

-- Degree
CREATE TABLE IF NOT EXISTS degree (
    degree_id VARCHAR(50) PRIMARY KEY,
    degree_name VARCHAR(100) NOT NULL,
    degree_type VARCHAR(50) NOT NULL,
    level_id VARCHAR(50),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (level_id) REFERENCES education_level(level_id) ON DELETE SET NULL
);

-- Education History
CREATE TABLE IF NOT EXISTS education_history (
    history_id VARCHAR(50) PRIMARY KEY,
    candidate_id VARCHAR(20) NOT NULL,
    school_id VARCHAR(50),
    major_id VARCHAR(50),
    level_id VARCHAR(50),
    degree_id VARCHAR(50),
    start_date DATE,
    end_date DATE,
    gpa FLOAT,
    achievements TEXT,
    is_current BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (candidate_id) REFERENCES candidate(candidate_id) ON DELETE CASCADE,
    FOREIGN KEY (school_id) REFERENCES school(school_id) ON DELETE SET NULL,
    FOREIGN KEY (major_id) REFERENCES major(major_id) ON DELETE SET NULL,
    FOREIGN KEY (level_id) REFERENCES education_level(level_id) ON DELETE SET NULL,
    FOREIGN KEY (degree_id) REFERENCES degree(degree_id) ON DELETE SET NULL
);

-- Candidate Credential
CREATE TABLE IF NOT EXISTS candidate_credential (
    credential_id VARCHAR(50) PRIMARY KEY,
    candidate_id VARCHAR(20) NOT NULL,
    credential_type VARCHAR(50) NOT NULL,
    credential_number VARCHAR(50) UNIQUE,
    issuing_authority VARCHAR(100),
    issue_date DATE,
    expiry_date DATE,
    status VARCHAR(20) DEFAULT 'valid',
    verification_status VARCHAR(20) DEFAULT 'pending',
    verified_by VARCHAR(50),
    verified_at TIMESTAMP WITH TIME ZONE,
    document_url TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (candidate_id) REFERENCES candidate(candidate_id) ON DELETE CASCADE
);

-- Candidate Exam
CREATE TABLE IF NOT EXISTS candidate_exam (
    candidate_exam_id VARCHAR(50) PRIMARY KEY,
    candidate_id VARCHAR(20) NOT NULL,
    exam_id VARCHAR(50) NOT NULL,
    registration_date TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) DEFAULT 'registered',
    application_number VARCHAR(50) UNIQUE,
    verification_status VARCHAR(20) DEFAULT 'pending',
    verified_by VARCHAR(50),
    verified_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (candidate_id) REFERENCES candidate(candidate_id) ON DELETE CASCADE,
    FOREIGN KEY (exam_id) REFERENCES exam(exam_id) ON DELETE CASCADE,
    UNIQUE (candidate_id, exam_id)
);

-- Certificate
CREATE TABLE IF NOT EXISTS certificate (
    certificate_id VARCHAR(50) PRIMARY KEY,
    candidate_exam_id VARCHAR(50) NOT NULL,
    certificate_name VARCHAR(100) NOT NULL,
    issuing_authority VARCHAR(100),
    issue_date DATE,
    expiry_date DATE,
    certificate_url TEXT,
    verification_status VARCHAR(20) DEFAULT 'pending',
    verified_by VARCHAR(50),
    verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (candidate_exam_id) REFERENCES candidate_exam(candidate_exam_id) ON DELETE CASCADE
);

-- Award
CREATE TABLE IF NOT EXISTS award (
    award_id VARCHAR(50) PRIMARY KEY,
    candidate_exam_id VARCHAR(50) NOT NULL,
    award_name VARCHAR(100) NOT NULL,
    issuing_organization VARCHAR(100),
    award_date DATE,
    award_description TEXT,
    verification_status VARCHAR(20) DEFAULT 'pending',
    verified_by VARCHAR(50),
    verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (candidate_exam_id) REFERENCES candidate_exam(candidate_exam_id) ON DELETE CASCADE
);

-- Achievement
CREATE TABLE IF NOT EXISTS achievement (
    achievement_id VARCHAR(50) PRIMARY KEY,
    candidate_exam_id VARCHAR(50) NOT NULL,
    achievement_type VARCHAR(50) NOT NULL,
    achievement_name VARCHAR(100) NOT NULL,
    achievement_date DATE,
    description TEXT,
    verification_status VARCHAR(20) DEFAULT 'pending',
    verified_by VARCHAR(50),
    verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (candidate_exam_id) REFERENCES candidate_exam(candidate_exam_id) ON DELETE CASCADE
);

-- Recognition
CREATE TABLE IF NOT EXISTS recognition (
    recognition_id VARCHAR(50) PRIMARY KEY,
    candidate_exam_id VARCHAR(50) NOT NULL,
    recognition_type VARCHAR(50) NOT NULL,
    recognition_name VARCHAR(100) NOT NULL,
    issuing_body VARCHAR(100),
    issue_date DATE,
    expiry_date DATE,
    verification_status VARCHAR(20) DEFAULT 'pending',
    verified_by VARCHAR(50),
    verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (candidate_exam_id) REFERENCES candidate_exam(candidate_exam_id) ON DELETE CASCADE
);

-- Candidate Exam Subject
CREATE TABLE IF NOT EXISTS candidate_exam_subject (
    id VARCHAR(50) PRIMARY KEY,
    candidate_exam_id VARCHAR(50) NOT NULL,
    exam_subject_id VARCHAR(50) NOT NULL,
    registration_date TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'registered',
    attended BOOLEAN DEFAULT FALSE,
    attendance_time TIMESTAMP WITH TIME ZONE,
    exam_room_id VARCHAR(50),
    seat_number VARCHAR(20),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (candidate_exam_id) REFERENCES candidate_exam(candidate_exam_id) ON DELETE CASCADE,
    FOREIGN KEY (exam_subject_id) REFERENCES exam_subject(exam_subject_id) ON DELETE CASCADE,
    FOREIGN KEY (exam_room_id) REFERENCES exam_room(room_id) ON DELETE SET NULL,
    UNIQUE (candidate_exam_id, exam_subject_id)
);

-- Exam Score
CREATE TABLE IF NOT EXISTS exam_score (
    score_id VARCHAR(50) PRIMARY KEY,
    candidate_exam_subject_id VARCHAR(50) NOT NULL,
    raw_score FLOAT,
    adjusted_score FLOAT,
    passing_threshold FLOAT,
    status VARCHAR(20),
    graded_by VARCHAR(50),
    graded_at TIMESTAMP WITH TIME ZONE,
    verified_by VARCHAR(50),
    verified_at TIMESTAMP WITH TIME ZONE,
    remarks TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (candidate_exam_subject_id) REFERENCES candidate_exam_subject(id) ON DELETE CASCADE
);

-- Exam Score History
CREATE TABLE IF NOT EXISTS exam_score_history (
    history_id VARCHAR(50) PRIMARY KEY,
    score_id VARCHAR(50) NOT NULL,
    previous_raw_score FLOAT,
    previous_adjusted_score FLOAT,
    new_raw_score FLOAT,
    new_adjusted_score FLOAT,
    reason TEXT NOT NULL,
    changed_by VARCHAR(50),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (score_id) REFERENCES exam_score(score_id) ON DELETE CASCADE
);

-- Score Review
CREATE TABLE IF NOT EXISTS score_review (
    review_id VARCHAR(50) PRIMARY KEY,
    score_id VARCHAR(50) NOT NULL,
    candidate_id VARCHAR(20) NOT NULL,
    request_date TIMESTAMP WITH TIME ZONE NOT NULL,
    request_reason TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    reviewer_id VARCHAR(50),
    review_date TIMESTAMP WITH TIME ZONE,
    original_score FLOAT,
    revised_score FLOAT,
    decision TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (score_id) REFERENCES exam_score(score_id) ON DELETE CASCADE,
    FOREIGN KEY (candidate_id) REFERENCES candidate(candidate_id) ON DELETE CASCADE
);

-- Exam Attempt History
CREATE TABLE IF NOT EXISTS exam_attempt_history (
    attempt_id VARCHAR(50) PRIMARY KEY,
    candidate_id VARCHAR(20) NOT NULL,
    exam_id VARCHAR(50) NOT NULL,
    attempt_number INTEGER NOT NULL,
    attempt_date DATE NOT NULL,
    result VARCHAR(20),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (candidate_id) REFERENCES candidate(candidate_id) ON DELETE CASCADE,
    FOREIGN KEY (exam_id) REFERENCES exam(exam_id) ON DELETE CASCADE
);

-- Add indexes for common search operations
CREATE INDEX IF NOT EXISTS idx_candidate_name ON candidate (full_name);
CREATE INDEX IF NOT EXISTS idx_personal_info_id_number ON personal_info (id_number);
CREATE INDEX IF NOT EXISTS idx_education_history_candidate ON education_history (candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidate_exam_candidate ON candidate_exam (candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidate_exam_exam ON candidate_exam (exam_id);
CREATE INDEX IF NOT EXISTS idx_exam_score_candidate ON exam_score (candidate_exam_subject_id);
CREATE INDEX IF NOT EXISTS idx_exam_schedule_exam ON exam_schedule (exam_id);
CREATE INDEX IF NOT EXISTS idx_exam_schedule_location ON exam_schedule (location_id);
CREATE INDEX IF NOT EXISTS idx_exam_schedule_date ON exam_schedule (start_time);

COMMIT;
"""
    return sql

if __name__ == "__main__":
    with open("sql_output/postgres_schema.sql", "w", encoding="utf-8") as f:
        sql = manually_create_sql()
        f.write(sql)
    print("PostgreSQL schema has been generated in sql_output/postgres_schema.sql") 