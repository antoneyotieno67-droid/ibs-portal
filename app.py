from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os

app = Flask(__name__)
app.secret_key = 'ibs-attendance-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ibs_attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# ─── Models ───────────────────────────────────────────────────────────────────

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    lecturer = db.Column(db.String(100), nullable=False)
    schedule = db.Column(db.String(100), nullable=True)
    students = db.relationship('Student', backref='course', lazy=True)
    sessions = db.relationship('Session', backref='course', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'{self.code} - {self.name}'


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reg_number = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    attendance_records = db.relationship('Attendance', backref='student', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'{self.name} ({self.reg_number})'


class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    topic = db.Column(db.String(200), nullable=True)
    start_time = db.Column(db.String(10), nullable=True)
    end_time = db.Column(db.String(10), nullable=True)
    attendance_records = db.relationship('Attendance', backref='session', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'Session {self.id} - {self.course.code} ({self.date})'


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    status = db.Column(db.String(10), nullable=False, default='present')  # present, absent, late, excused
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'{self.student.name} - {self.status}'


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    courses = Course.query.all()
    total_students = Student.query.count()
    total_sessions = Session.query.count()
    total_attendance = Attendance.query.count()
    return render_template('index.html', courses=courses, total_students=total_students,
                           total_sessions=total_sessions, total_attendance=total_attendance)


# ─── Course Management ────────────────────────────────────────────────────────

@app.route('/courses')
def courses():
    all_courses = Course.query.all()
    return render_template('courses.html', courses=all_courses)


@app.route('/courses/add', methods=['POST'])
def add_course():
    name = request.form.get('name')
    code = request.form.get('code')
    lecturer = request.form.get('lecturer')
    schedule = request.form.get('schedule')

    if not name or not code or not lecturer:
        flash('Course name, code, and lecturer are required!', 'danger')
        return redirect(url_for('courses'))

    existing = Course.query.filter_by(code=code).first()
    if existing:
        flash(f'Course with code {code} already exists!', 'danger')
        return redirect(url_for('courses'))

    course = Course(name=name, code=code, lecturer=lecturer, schedule=schedule)
    db.session.add(course)
    db.session.commit()
    flash(f'Course {name} added successfully!', 'success')
    return redirect(url_for('courses'))


@app.route('/courses/<int:course_id>/edit', methods=['POST'])
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    course.name = request.form.get('name', course.name)
    course.lecturer = request.form.get('lecturer', course.lecturer)
    course.schedule = request.form.get('schedule', course.schedule)
    db.session.commit()
    flash('Course updated successfully!', 'success')
    return redirect(url_for('courses'))


@app.route('/courses/<int:course_id>/delete', methods=['POST'])
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash('Course deleted successfully!', 'success')
    return redirect(url_for('courses'))


# ─── Student Management ──────────────────────────────────────────────────────

@app.route('/students')
def students():
    all_students = Student.query.all()
    courses = Course.query.all()
    return render_template('students.html', students=all_students, courses=courses)


@app.route('/students/add', methods=['POST'])
def add_student():
    reg_number = request.form.get('reg_number')
    name = request.form.get('name')
    email = request.form.get('email')
    course_id = request.form.get('course_id')

    if not reg_number or not name or not course_id:
        flash('Registration number, name, and course are required!', 'danger')
        return redirect(url_for('students'))

    existing = Student.query.filter_by(reg_number=reg_number).first()
    if existing:
        flash(f'Student with registration number {reg_number} already exists!', 'danger')
        return redirect(url_for('students'))

    student = Student(reg_number=reg_number, name=name, email=email, course_id=course_id)
    db.session.add(student)
    db.session.commit()
    flash(f'Student {name} added successfully!', 'success')
    return redirect(url_for('students'))


@app.route('/students/<int:student_id>/edit', methods=['POST'])
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    student.name = request.form.get('name', student.name)
    student.email = request.form.get('email', student.email)
    student.course_id = request.form.get('course_id', student.course_id)
    db.session.commit()
    flash('Student updated successfully!', 'success')
    return redirect(url_for('students'))


@app.route('/students/<int:student_id>/delete', methods=['POST'])
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted successfully!', 'success')
    return redirect(url_for('students'))


# ─── Session & Attendance ─────────────────────────────────────────────────────

@app.route('/attendance')
def attendance():
    courses = Course.query.all()
    return render_template('attendance.html', courses=courses)


@app.route('/attendance/course/<int:course_id>')
def course_sessions(course_id):
    course = Course.query.get_or_404(course_id)
    sessions = Session.query.filter_by(course_id=course_id).order_by(Session.date.desc()).all()
    return render_template('sessions.html', course=course, sessions=sessions)


@app.route('/attendance/session/new/<int:course_id>', methods=['GET', 'POST'])
def new_session(course_id):
    course = Course.query.get_or_404(course_id)
    if request.method == 'POST':
        session_date_str = request.form.get('date', str(date.today()))
        topic = request.form.get('topic', '')
        start_time = request.form.get('start_time', '')
        end_time = request.form.get('end_time', '')
        try:
            session_date = datetime.strptime(session_date_str, '%Y-%m-%d').date()
        except ValueError:
            session_date = date.today()

        session = Session(course_id=course_id, date=session_date, topic=topic,
                          start_time=start_time, end_time=end_time)
        db.session.add(session)
        db.session.commit()
        return redirect(url_for('take_attendance', session_id=session.id))

    return render_template('new_session.html', course=course)


@app.route('/attendance/take/<int:session_id>', methods=['GET', 'POST'])
def take_attendance(session_id):
    session = Session.query.get_or_404(session_id)
    course = session.course
    students = Student.query.filter_by(course_id=course.id).all()

    if request.method == 'POST':
        # Clear existing attendance for this session
        Attendance.query.filter_by(session_id=session_id).delete()
        for student in students:
            status = request.form.get(f'status_{student.id}', 'absent')
            att = Attendance(student_id=student.id, session_id=session_id, status=status)
            db.session.add(att)
        db.session.commit()
        flash(f'Attendance for {course.code} on {session.date} saved!', 'success')
        return redirect(url_for('view_attendance', session_id=session_id))

    # Check if attendance already exists
    existing_records = Attendance.query.filter_by(session_id=session_id).all()
    attendance_map = {r.student_id: r.status for r in existing_records}

    return render_template('take_attendance.html', session=session, course=course,
                           students=students, attendance_map=attendance_map)


@app.route('/attendance/view/<int:session_id>')
def view_attendance(session_id):
    session = Session.query.get_or_404(session_id)
    course = session.course
    records = Attendance.query.filter_by(session_id=session_id).all()
    return render_template('view_attendance.html', session=session, course=course, records=records)


@app.route('/attendance/session/<int:session_id>/delete', methods=['POST'])
def delete_session(session_id):
    session = Session.query.get_or_404(session_id)
    course_id = session.course_id
    db.session.delete(session)
    db.session.commit()
    flash('Session deleted!', 'success')
    return redirect(url_for('course_sessions', course_id=course_id))


# ─── Reports ──────────────────────────────────────────────────────────────────

@app.route('/reports')
def reports():
    courses = Course.query.all()
    return render_template('reports.html', courses=courses)


@app.route('/reports/course/<int:course_id>')
def course_report(course_id):
    course = Course.query.get_or_404(course_id)
    students = Student.query.filter_by(course_id=course_id).all()
    sessions = Session.query.filter_by(course_id=course_id).order_by(Session.date).all()

    report_data = []
    for student in students:
        total = len(sessions)
        present = Attendance.query.filter_by(student_id=student.id, status='present').count()
        late = Attendance.query.filter_by(student_id=student.id, status='late').count()
        absent = Attendance.query.filter_by(student_id=student.id, status='absent').count()
        excused = Attendance.query.filter_by(student_id=student.id, status='excused').count()
        attended = present + late
        percentage = round((attended / total * 100), 1) if total > 0 else 0
        report_data.append({
            'student': student,
            'total': total,
            'present': present,
            'late': late,
            'absent': absent,
            'excused': excused,
            'percentage': percentage
        })

    return render_template('course_report.html', course=course, sessions=sessions, report_data=report_data)


@app.route('/api/stats')
def api_stats():
    total_students = Student.query.count()
    total_courses = Course.query.count()
    total_sessions = Session.query.count()
    total_attendance = Attendance.query.count()

    present_count = Attendance.query.filter_by(status='present').count()
    absent_count = Attendance.query.filter_by(status='absent').count()
    late_count = Attendance.query.filter_by(status='late').count()

    return jsonify({
        'total_students': total_students,
        'total_courses': total_courses,
        'total_sessions': total_sessions,
        'total_attendance': total_attendance,
        'present': present_count,
        'absent': absent_count,
        'late': late_count
    })


# ─── Init DB ──────────────────────────────────────────────────────────────────

with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)