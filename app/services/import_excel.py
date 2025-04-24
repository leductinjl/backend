"""
Excel import service module.

This module provides functionality to import data from Excel files
into the database models.
"""

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.domain.models.candidate import Candidate
from app.domain.models.personal_info import PersonalInfo
from app.domain.models.exam_score import ExamScore
from app.domain.models.exam_subject import ExamSubject
from app.domain.models.exam import Exam
from app.domain.models.subject import Subject
from app.domain.models.candidate_exam import CandidateExam
from app.domain.models.candidate_exam_subject import CandidateExamSubject
from app.services.id_service import generate_model_id
from datetime import datetime, date
import logging
from app.domain.models.exam_type import ExamType
from app.domain.models.candidate_exam_subject import RegistrationStatus
import uuid
import asyncio
from typing import Dict, List, Tuple
from app.domain.models.management_unit import ManagementUnit

logger = logging.getLogger(__name__)

BATCH_SIZE = 100  # Process 100 records at a time

async def import_excel_data(db: AsyncSession, excel_path: str):
    """
    Import data from Excel file with 2 sheets into database.
    
    Sheet 1 (Scores):
    - Mã SV, Họ và tên, Năm học, Học kỳ
    - Mã học phần, Tên học phần, Số TC
    - Điểm giữa kỳ, Điểm cuối kỳ, Điểm trung bình, Tổng kết chữ, Đạt
    
    Sheet 2 (Student Info):
    - MSSV, Họ và tên, Ngày sinh
    - Địa chỉ thường trú, Phường xã, Tỉnh thành, Quận huyện
    - CMND
    
    Args:
        db: Database session
        excel_path: Path to Excel file
    """
    try:
        logger.info(f"Starting import from Excel file: {excel_path}")
        
        # Read both sheets
        try:
            df_scores = pd.read_excel(excel_path, sheet_name=0)  # Sheet 1: Scores
            df_student_info = pd.read_excel(excel_path, sheet_name=1)  # Sheet 2: Student info
            logger.info("Successfully read Excel sheets")
        except Exception as e:
            logger.error(f"Error reading Excel file: {str(e)}")
            return False, f"Error reading Excel file: {str(e)}"
        
        # Validate required columns
        required_score_columns = ['Mã SV', 'Họ và tên', 'Năm học', 'Học kỳ', 'Mã học phần', 'Tên học phần', 'Số TC']
        required_student_columns = ['MSSV', 'Họ và tên', 'Ngày sinh', 'Địa chỉ thường trú', 'Phường xã', 'Tỉnh thành', 'Quận huyện', 'CMND']
        
        missing_score_columns = [col for col in required_score_columns if col not in df_scores.columns]
        missing_student_columns = [col for col in required_student_columns if col not in df_student_info.columns]
        
        if missing_score_columns or missing_student_columns:
            error_msg = "Missing required columns: "
            if missing_score_columns:
                error_msg += f"Scores sheet: {', '.join(missing_score_columns)}. "
            if missing_student_columns:
                error_msg += f"Student info sheet: {', '.join(missing_student_columns)}"
            logger.error(error_msg)
            return False, error_msg
        
        # Create a mapping of MSSV to generated candidate_id
        mssv_to_candidate_id: Dict[str, str] = {}
        
        # Process student info first
        logger.info("Processing student information...")
        total_students = len(df_student_info)
        processed_students = 0
        
        for i in range(0, total_students, BATCH_SIZE):
            batch = df_student_info.iloc[i:i+BATCH_SIZE]
            for _, row in batch.iterrows():
                try:
                    mssv = str(row['MSSV'])
                    
                    # Check if we already have a candidate_id for this MSSV
                    if mssv not in mssv_to_candidate_id:
                        # Generate a new candidate_id
                        candidate_id = generate_model_id("Candidate")
                        mssv_to_candidate_id[mssv] = candidate_id
                    else:
                        candidate_id = mssv_to_candidate_id[mssv]
                    
                    # Create or update Candidate
                    result = await db.execute(
                        select(Candidate).where(Candidate.candidate_id == candidate_id)
                    )
                    candidate = result.scalar_one_or_none()
                    
                    if not candidate:
                        candidate = Candidate(
                            candidate_id=candidate_id,
                            full_name=row['Họ và tên']
                        )
                        db.add(candidate)
                    
                    # Convert date string to date object
                    try:
                        birth_date = datetime.strptime(str(row['Ngày sinh']), '%d/%m/%Y').date()
                    except ValueError:
                        try:
                            birth_date = datetime.strptime(str(row['Ngày sinh']), '%Y-%m-%d').date()
                        except ValueError:
                            logger.error(f"Invalid date format for student {mssv}: {row['Ngày sinh']}")
                            continue
                    
                    # Process ID number to ensure it fits in VARCHAR(12)
                    id_number = str(row['CMND']) if pd.notna(row['CMND']) else None
                    if id_number:
                        # Remove decimal point and trailing zeros
                        id_number = id_number.replace('.0', '').replace('.', '')
                        if len(id_number) > 12:
                            logger.warning(f"ID number {id_number} is too long for student {mssv}, truncating to 12 characters")
                            id_number = id_number[:12]
                    
                    # Combine address fields
                    address = f"{row['Địa chỉ thường trú']}, {row['Phường xã']}, {row['Quận huyện']}, {row['Tỉnh thành']}"
                    
                    # Create or update PersonalInfo
                    result = await db.execute(
                        select(PersonalInfo).where(PersonalInfo.id_number == str(row['CMND']))
                    )
                    existing_personal_info = result.scalar_one_or_none()
                    
                    if existing_personal_info:
                        # Update existing personal info
                        existing_personal_info.candidate_id = candidate_id
                        existing_personal_info.birth_date = birth_date
                        existing_personal_info.primary_address = address
                        existing_personal_info.updated_at = datetime.now()
                    else:
                        # Create new personal info
                        personal_info = PersonalInfo(
                            candidate_id=candidate_id,
                            birth_date=birth_date,
                            id_number=str(row['CMND']),
                            phone_number=None,
                            email=None,
                            primary_address=address,
                            secondary_address=None,
                            id_card_image_url=None,
                            candidate_card_image_url=None,
                            face_recognition_data_url=None,
                            updated_at=datetime.now()
                        )
                        db.add(personal_info)
                except Exception as e:
                    logger.error(f"Error processing student {mssv}: {str(e)}")
                    await db.rollback()
                    return False, f"Error processing student {mssv}: {str(e)}"
            
            # Commit after each batch
            await db.commit()
            processed_students += len(batch)
            logger.info(f"Processed {processed_students}/{total_students} students")
        
        # First, create all unique subjects
        logger.info("Processing subjects...")
        unique_subjects = df_scores[['Mã học phần', 'Tên học phần']].drop_duplicates()
        for _, row in unique_subjects.iterrows():
            try:
                result = await db.execute(
                    select(Subject).where(Subject.subject_code == str(row['Mã học phần']))
                )
                subject = result.scalar_one_or_none()
                
                if not subject:
                    subject = Subject(
                        subject_code=str(row['Mã học phần']),
                        subject_name=row['Tên học phần']
                    )
                    db.add(subject)
            except Exception as e:
                logger.error(f"Error processing subject {row['Mã học phần']}: {str(e)}")
                await db.rollback()
                return False, f"Error processing subject {row['Mã học phần']}: {str(e)}"
        
        # Then, create all unique exams
        logger.info("Processing exams...")
        unique_exams = df_scores[['Năm học', 'Học kỳ']].drop_duplicates()
        
        # Get or create default exam type
        result = await db.execute(
            select(ExamType).where(ExamType.type_name == "Học kỳ")
        )
        exam_type = result.scalar_one_or_none()
        
        if not exam_type:
            exam_type = ExamType(
                type_id=generate_model_id("ExamType"),
                type_name="Học kỳ",
                description="Kỳ thi học kỳ thông thường",
                is_active=True
            )
            db.add(exam_type)
            await db.commit()
        
        # Get or create default management unit
        result = await db.execute(
            select(ManagementUnit).where(ManagementUnit.unit_name == "Phòng Đào tạo")
        )
        management_unit = result.scalar_one_or_none()
        
        if not management_unit:
            management_unit = ManagementUnit(
                unit_id=generate_model_id("ManagementUnit"),
                unit_name="Phòng Đào tạo",
                unit_type="Academic"
            )
            db.add(management_unit)
            await db.commit()
        
        for _, row in unique_exams.iterrows():
            try:
                # Use simple format for exam name to avoid encoding issues
                exam_name = f"Học kỳ {row['Học kỳ']} năm học {row['Năm học']}"
                result = await db.execute(
                    select(Exam).where(Exam.exam_name == exam_name)
                )
                exam = result.scalar_one_or_none()
                
                if not exam:
                    # Generate exam_id using the same pattern as other IDs
                    exam_id = generate_model_id("Exam")
                    exam = Exam(
                        exam_id=exam_id,
                        exam_name=exam_name,
                        type_id=exam_type.type_id,  # Use the default exam type
                        start_date=datetime.strptime(f"{row['Năm học'].split('-')[0]}-09-01", "%Y-%m-%d").date(),
                        end_date=datetime.strptime(f"{row['Năm học'].split('-')[1]}-01-31", "%Y-%m-%d").date(),
                        scope="School",
                        is_active=True,
                        organizing_unit_id=management_unit.unit_id  # Link to management unit
                    )
                    db.add(exam)
            except Exception as e:
                logger.error(f"Error processing exam {exam_name}: {str(e)}")
                await db.rollback()
                return False, f"Error processing exam {exam_name}: {str(e)}"
        
        # Commit to save subjects and exams
        await db.commit()
        logger.info("Successfully saved subjects and exams")
        
        # Now process scores and create relationships
        logger.info("Processing scores and relationships...")
        total_scores = len(df_scores)
        processed_scores = 0
        
        for i in range(0, total_scores, BATCH_SIZE):
            batch = df_scores.iloc[i:i+BATCH_SIZE]
            for _, row in batch.iterrows():
                try:
                    mssv = str(row['Mã SV'])
                    if mssv not in mssv_to_candidate_id:
                        logger.error(f"MSSV {mssv} not found in student info sheet")
                        continue
                    candidate_id = mssv_to_candidate_id[mssv]
                    
                    # Get the subject
                    result = await db.execute(
                        select(Subject).where(Subject.subject_code == str(row['Mã học phần']))
                    )
                    subject = result.scalar_one_or_none()
                    
                    # Get the exam
                    exam_name = f"Học kỳ {row['Học kỳ']} năm học {row['Năm học']}"
                    result = await db.execute(
                        select(Exam).where(Exam.exam_name == exam_name)
                    )
                    exam = result.scalar_one_or_none()
                    
                    # Create ExamSubject (link between Exam and Subject)
                    result = await db.execute(
                        select(ExamSubject).where(
                            ExamSubject.exam_id == exam.exam_id,
                            ExamSubject.subject_id == subject.subject_id
                        )
                    )
                    exam_subject = result.scalar_one_or_none()
                    
                    if not exam_subject:
                        exam_subject_id = generate_model_id("ExamSubject")
                        exam_subject = ExamSubject(
                            exam_subject_id=exam_subject_id,
                            exam_id=exam.exam_id,
                            subject_id=subject.subject_id,
                            weight=1.0,
                            max_score=100.0,
                            is_required=True,
                            subject_metadata={
                                "credits": row['Số TC']
                            }
                        )
                        db.add(exam_subject)
                    
                    # Create CandidateExam (link between Candidate and Exam)
                    result = await db.execute(
                        select(CandidateExam).where(
                            CandidateExam.candidate_id == candidate_id,
                            CandidateExam.exam_id == exam.exam_id
                        )
                    )
                    candidate_exam = result.scalar_one_or_none()
                    
                    if not candidate_exam:
                        candidate_exam = CandidateExam(
                            candidate_id=candidate_id,
                            exam_id=exam.exam_id,
                            status="Attended",
                            registration_date=datetime.now().date()
                        )
                        db.add(candidate_exam)
                    
                    # Create CandidateExamSubject (link between candidate and exam subject)
                    result = await db.execute(
                        select(CandidateExamSubject).where(
                            CandidateExamSubject.candidate_exam_id == candidate_exam.candidate_exam_id,
                            CandidateExamSubject.exam_subject_id == exam_subject.exam_subject_id
                        )
                    )
                    candidate_exam_subject = result.scalar_one_or_none()
                    
                    if not candidate_exam_subject:
                        candidate_exam_subject_id = generate_model_id("CandidateExamSubject")
                        candidate_exam_subject = CandidateExamSubject(
                            candidate_exam_subject_id=candidate_exam_subject_id,
                            candidate_exam_id=candidate_exam.candidate_exam_id,
                            exam_subject_id=exam_subject.exam_subject_id,
                            status=RegistrationStatus.REGISTERED,
                            is_required=True
                        )
                        db.add(candidate_exam_subject)
                    
                    # Create ExamScore with proper relationships
                    exam_score_id = f"SCORE_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
                    
                    # Handle NaN score value
                    final_score = row['Điểm cuối kỳ'] if pd.notna(row['Điểm cuối kỳ']) else None
                    
                    exam_score = ExamScore(
                        exam_score_id=exam_score_id,
                        exam_subject_id=exam_subject.exam_subject_id,
                        candidate_exam_subject_id=candidate_exam_subject.candidate_exam_subject_id,
                        score=final_score,
                        status="graded"
                    )
                    db.add(exam_score)
                except Exception as e:
                    logger.error(f"Error processing score for student {mssv} in subject {row['Mã học phần']}: {str(e)}")
                    await db.rollback()
                    return False, f"Error processing score for student {mssv} in subject {row['Mã học phần']}: {str(e)}"
            
            # Commit after each batch
            await db.commit()
            processed_scores += len(batch)
            logger.info(f"Processed {processed_scores}/{total_scores} scores")
        
        logger.info("Import completed successfully")
        return True, "Import successful"
        
    except Exception as e:
        logger.error(f"Error during import: {str(e)}", exc_info=True)
        await db.rollback()
        return False, f"Import failed: {str(e)}" 