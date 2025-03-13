```sql
-- 1. Thông tin cơ bản thí sinh
CREATE TABLE candidate (
    candidate_id VARCHAR(50) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL
);

-- 2. Thông tin cá nhân chi tiết
CREATE TABLE personal_info (
    candidate_id VARCHAR(50) PRIMARY KEY,
    birth_date DATE NOT NULL,
    id_number VARCHAR(12) UNIQUE,
    phone_number VARCHAR(15),
    email VARCHAR(100),
    primary_address TEXT,
    secondary_address TEXT,
    id_card_image_url TEXT,
    candidate_card_image_url TEXT,
    face_recognition_data_url TEXT,
    FOREIGN KEY (candidate_id) REFERENCES candidate(candidate_id)
);

-- 3. Đơn vị quản lý
CREATE TABLE management_unit (
    unit_id VARCHAR(50) PRIMARY KEY,
    unit_name VARCHAR(100) NOT NULL,
    unit_type VARCHAR(50) NOT NULL, -- Department, Ministry, University Group
    additional_info TEXT
);

-- 4. Trường học
CREATE TABLE school (
    school_id VARCHAR(50) PRIMARY KEY,
    school_name VARCHAR(150) NOT NULL,
    address TEXT,
    unit_id VARCHAR(50),
    education_level VARCHAR(50), -- Primary, Secondary, High School, University
    FOREIGN KEY (unit_id) REFERENCES management_unit(unit_id)
);

-- 5. Ngành học
CREATE TABLE major (
    major_id VARCHAR(50) PRIMARY KEY,
    major_name VARCHAR(150) NOT NULL,
    ministry_code VARCHAR(20), -- Ministry's major code (if any)
    education_level VARCHAR(50), -- Bachelor, Master, PhD
    description TEXT
);

-- 6. Liên kết trường và ngành đào tạo
CREATE TABLE school_major (
    school_major_id VARCHAR(50) PRIMARY KEY,
    school_id VARCHAR(50) NOT NULL,
    major_id VARCHAR(50) NOT NULL,
    start_year INT, -- Năm bắt đầu đào tạo ngành này
    additional_info TEXT,
    FOREIGN KEY (school_id) REFERENCES school(school_id),
    FOREIGN KEY (major_id) REFERENCES major(major_id),
    UNIQUE(school_id, major_id)
);

-- 7. Môn học
CREATE TABLE subject (
    subject_id VARCHAR(50) PRIMARY KEY,
    subject_name VARCHAR(100) NOT NULL,
    education_level VARCHAR(50), -- Secondary, High School, University
    description TEXT
);

-- 8. Liên kết ngành học và môn học
CREATE TABLE major_subject (
    major_subject_id VARCHAR(50) PRIMARY KEY,
    major_id VARCHAR(50) NOT NULL,
    subject_id VARCHAR(50) NOT NULL,
    is_mandatory BOOLEAN DEFAULT TRUE,
    credits INT, -- Số tín chỉ (cho đại học)
    FOREIGN KEY (major_id) REFERENCES major(major_id),
    FOREIGN KEY (subject_id) REFERENCES subject(subject_id),
    UNIQUE(major_id, subject_id)
);

-- 9. Bằng cấp đại học trở lên
CREATE TABLE degree (
    degree_id VARCHAR(50) PRIMARY KEY,
    candidate_id VARCHAR(50) NOT NULL,
    school_id VARCHAR(50) NOT NULL,
    major_id VARCHAR(50) NOT NULL,
    education_level VARCHAR(50) NOT NULL, -- Bachelor, Master, PhD
    start_year INT,
    end_year INT,
    academic_performance VARCHAR(20), -- Good, Excellent
    degree_image_url TEXT,
    additional_info TEXT,
    FOREIGN KEY (candidate_id) REFERENCES candidate(candidate_id),
    FOREIGN KEY (school_id) REFERENCES school(school_id),
    FOREIGN KEY (major_id) REFERENCES major(major_id)
);

-- 10. Lịch sử học tập (tiểu học, THCS, THPT)
CREATE TABLE education_history (
    education_history_id VARCHAR(50) PRIMARY KEY,
    candidate_id VARCHAR(50) NOT NULL,
    school_id VARCHAR(50) NOT NULL,
    education_level VARCHAR(50) NOT NULL, -- Primary, Secondary, High School
    start_year INT,
    end_year INT,
    academic_performance VARCHAR(20), -- Good, Excellent
    additional_info TEXT,
    related_degree_id VARCHAR(50), -- Liên kết đến bằng cấp nếu có
    FOREIGN KEY (candidate_id) REFERENCES candidate(candidate_id),
    FOREIGN KEY (school_id) REFERENCES school(school_id),
    FOREIGN KEY (related_degree_id) REFERENCES degree(degree_id)
);

-- 11. Loại kỳ thi
CREATE TABLE exam_type (
    type_id VARCHAR(50) PRIMARY KEY,
    type_name VARCHAR(100) NOT NULL, -- Semester, Certificate, Competition
    description TEXT
);

-- 12. Địa điểm thi
CREATE TABLE exam_location (
    location_id VARCHAR(50) PRIMARY KEY,
    location_name VARCHAR(100) NOT NULL,
    address TEXT NOT NULL,
    capacity INT, -- Sức chứa
    additional_info TEXT
);

-- 13. Kỳ thi
CREATE TABLE exam (
    exam_id VARCHAR(50) PRIMARY KEY,
    exam_name VARCHAR(200) NOT NULL,
    type_id VARCHAR(50) NOT NULL,
    start_date DATE,
    end_date DATE,
    scope VARCHAR(50), -- School, Provincial, National, International
    education_level VARCHAR(50), -- Secondary, High School, University
    organizing_unit_id VARCHAR(50), -- Đơn vị tổ chức
    primary_location_id VARCHAR(50), -- Địa điểm tổ chức chính
    additional_info TEXT,
    FOREIGN KEY (type_id) REFERENCES exam_type(type_id),
    FOREIGN KEY (organizing_unit_id) REFERENCES management_unit(unit_id),
    FOREIGN KEY (primary_location_id) REFERENCES exam_location(location_id)
);

-- 14. Liên kết kỳ thi với nhiều địa điểm
CREATE TABLE exam_location_mapping (
    mapping_id VARCHAR(50) PRIMARY KEY,
    exam_id VARCHAR(50) NOT NULL,
    location_id VARCHAR(50) NOT NULL,
    additional_info TEXT,
    FOREIGN KEY (exam_id) REFERENCES exam(exam_id),
    FOREIGN KEY (location_id) REFERENCES exam_location(location_id),
    UNIQUE(exam_id, location_id)
);

-- 15. Phòng thi
CREATE TABLE exam_room (
    room_id VARCHAR(50) PRIMARY KEY,
    room_name VARCHAR(50) NOT NULL,
    location_id VARCHAR(50) NOT NULL,
    capacity INT, -- Sức chứa
    additional_info TEXT,
    FOREIGN KEY (location_id) REFERENCES exam_location(location_id)
);

-- 16. Liên kết kỳ thi và môn thi
CREATE TABLE exam_subject (
    exam_subject_id VARCHAR(50) PRIMARY KEY,
    exam_id VARCHAR(50) NOT NULL,
    subject_id VARCHAR(50) NOT NULL,
    exam_date DATE,
    duration_minutes INT,
    room_id VARCHAR(50), -- Phòng thi cho môn này
    additional_info TEXT,
    FOREIGN KEY (exam_id) REFERENCES exam(exam_id),
    FOREIGN KEY (subject_id) REFERENCES subject(subject_id),
    FOREIGN KEY (room_id) REFERENCES exam_room(room_id)
);

-- 17. Thông tin tham gia kỳ thi
CREATE TABLE candidate_exam (
    candidate_exam_id VARCHAR(50) PRIMARY KEY,
    candidate_id VARCHAR(50) NOT NULL,
    exam_id VARCHAR(50) NOT NULL,
    registration_number VARCHAR(20),
    registration_date DATE,
    status VARCHAR(50), -- Registered, Attended, Absent
    room_id VARCHAR(50), -- Phòng thi
    attempt_number INT DEFAULT 1, -- Số lần thi
    FOREIGN KEY (candidate_id) REFERENCES candidate(candidate_id),
    FOREIGN KEY (exam_id) REFERENCES exam(exam_id),
    FOREIGN KEY (room_id) REFERENCES exam_room(room_id)
);

-- 18. Điểm thi
CREATE TABLE exam_score (
    exam_score_id VARCHAR(50) PRIMARY KEY,
    candidate_id VARCHAR(50) NOT NULL,
    exam_id VARCHAR(50) NOT NULL,
    subject_id VARCHAR(50) NOT NULL,
    score DECIMAL(5,2),
    additional_info TEXT,
    FOREIGN KEY (candidate_id) REFERENCES candidate(candidate_id),
    FOREIGN KEY (exam_id) REFERENCES exam(exam_id),
    FOREIGN KEY (subject_id) REFERENCES subject(subject_id)
);

-- 19. Lịch sử thay đổi điểm
CREATE TABLE exam_score_history (
    history_id VARCHAR(50) PRIMARY KEY,
    score_id VARCHAR(50) NOT NULL, -- ID của điểm thi trong bảng exam_score
    previous_score DECIMAL(5,2),
    new_score DECIMAL(5,2),
    change_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    change_reason VARCHAR(200), -- Lý do thay đổi
    changed_by VARCHAR(50), -- Người thay đổi
    FOREIGN KEY (score_id) REFERENCES exam_score(exam_score_id)
);

-- 20. Phúc khảo
CREATE TABLE score_review (
    score_review_id VARCHAR(50) PRIMARY KEY,
    score_id VARCHAR(50) NOT NULL, -- ID của điểm thi
    request_date DATE NOT NULL,
    review_status VARCHAR(50) NOT NULL, -- Pending, Approved, Rejected
    original_score DECIMAL(5,2),
    reviewed_score DECIMAL(5,2),
    review_result TEXT, -- Kết quả phúc khảo
    review_date DATE,
    additional_info TEXT,
    FOREIGN KEY (score_id) REFERENCES exam_score(exam_score_id)
);

-- 21. Lịch sử thi cử
CREATE TABLE exam_attempt_history (
    attempt_history_id VARCHAR(50) PRIMARY KEY,
    candidate_id VARCHAR(50) NOT NULL,
    exam_id VARCHAR(50) NOT NULL,
    attempt_number INT NOT NULL,
    attempt_date DATE NOT NULL,
    result VARCHAR(50), -- Pass, Fail
    notes TEXT,
    FOREIGN KEY (candidate_id) REFERENCES candidate(candidate_id),
    FOREIGN KEY (exam_id) REFERENCES exam(exam_id)
);

-- 22. Chứng chỉ
CREATE TABLE certificate (
    certificate_id VARCHAR(50) PRIMARY KEY,
    candidate_id VARCHAR(50) NOT NULL,
    exam_id VARCHAR(50) NOT NULL,
    certificate_number VARCHAR(50),
    issue_date DATE,
    score VARCHAR(20), -- Có thể là số hoặc chữ (ví dụ: IELTS 7.5, TOEIC 850)
    expiry_date DATE,
    certificate_image_url TEXT,
    additional_info TEXT,
    FOREIGN KEY (candidate_id) REFERENCES candidate(candidate_id),
    FOREIGN KEY (exam_id) REFERENCES exam(exam_id)
);

-- 23. Chứng nhận
CREATE TABLE recognition (
    recognition_id VARCHAR(50) PRIMARY KEY,
    candidate_id VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    issuing_organization VARCHAR(100) NOT NULL,
    issue_date DATE,
    recognition_type VARCHAR(50), -- Completion, Participation, Appreciation
    related_exam_id VARCHAR(50), -- Liên kết với kỳ thi nếu có
    recognition_image_url TEXT,
    description TEXT,
    additional_info TEXT,
    FOREIGN KEY (candidate_id) REFERENCES candidate(candidate_id),
    FOREIGN KEY (related_exam_id) REFERENCES exam(exam_id)
);

-- 24. Giải thưởng
CREATE TABLE award (
    award_id VARCHAR(50) PRIMARY KEY,
    candidate_id VARCHAR(50) NOT NULL,
    exam_id VARCHAR(50) NOT NULL,
    award_type VARCHAR(50), -- First, Second, Third, Gold Medal, Silver Medal
    achievement VARCHAR(100), -- Specific achievement if any
    certificate_image_url TEXT,
    education_level VARCHAR(50), -- Bậc học khi đạt giải
    award_date DATE,
    additional_info TEXT,
    FOREIGN KEY (candidate_id) REFERENCES candidate(candidate_id),
    FOREIGN KEY (exam_id) REFERENCES exam(exam_id)
);

-- 25. Thành tích
CREATE TABLE achievement (
    achievement_id VARCHAR(50) PRIMARY KEY,
    candidate_id VARCHAR(50) NOT NULL,
    achievement_name VARCHAR(200) NOT NULL,
    achievement_type VARCHAR(50), -- Research, Community Service, Sports, Arts
    description TEXT,
    achievement_date DATE,
    organization VARCHAR(100), -- Tổ chức ghi nhận thành tích
    proof_url TEXT, -- URL chứng minh thành tích
    education_level VARCHAR(50), -- Bậc học khi đạt thành tích
    additional_info TEXT,
    FOREIGN KEY (candidate_id) REFERENCES candidate(candidate_id)
);
```

Mô hình dữ liệu quan hệ này đã được thiết kế để:

1. Lưu trữ thông tin đầy đủ về thí sinh, quá trình học tập và thành tích
2. Theo dõi chi tiết các kỳ thi, điểm thi, chứng chỉ và giải thưởng
3. Thiết lập mối liên kết giữa các thực thể để phục vụ truy vấn hiệu quả
4. Tránh tham chiếu vòng tròn (circular references)
5. Dễ dàng đồng bộ sang Neo4j để xây dựng đồ thị tri thức

Mô hình này phù hợp để lưu trữ trong PostgreSQL và sau đó đồng bộ sang Neo4j để phục vụ mục đích truy vấn và tra cứu thông tin thí sinh.
