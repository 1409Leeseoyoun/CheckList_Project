from flask import (
    Flask,               # Flask 클래스를 불러와 Flask 애플리케이션을 설정
    render_template,     # HTML 템플릿을 렌더링하기 위한 함수
    request,             # 클라이언트 요청 데이터를 가져오기 위한 함수
    jsonify,             # JSON 형태로 응답을 반환하기 위한 함수
    redirect,            # URL 리디렉션을 위한 함수
    url_for,             # URL을 동적으로 생성하기 위한 함수
    session,             # 세션 관리를 위한 객체
)
import sqlite3           # SQLite 데이터베이스에 접근하기 위한 라이브러리
import logging           # 로깅을 위한 라이브러리

logging.basicConfig(
    level=logging.INFO,  # 로깅의 기본 수준을 INFO로 설정
    format="%(asctime)s - %(levelname)s - %(message)s"  # 로깅 포맷 설정
)

app = Flask(__name__)    # Flask 애플리케이션 인스턴스를 생성
app.secret_key = "your_secret_key"  # 세션에 필요한 비밀 키 설정
DATABASE = "users.db"    # SQLite 데이터베이스 파일명 설정


def get_db():
    """ 데이터베이스 연결 함수 """
    conn = sqlite3.connect(DATABASE)  # DATABASE에 연결
    conn.row_factory = sqlite3.Row    # 행 결과를 딕셔너리 형식으로 반환
    return conn  # 연결 객체 반환


def init_db():
    """ 데이터베이스 초기화 함수 """
    with get_db() as db:  # 데이터베이스 연결 후
        db.execute(
            """CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL
                      )"""
        )  # users 테이블이 없으면 생성 (id, username, password 포함)
        db.execute(
            """CREATE TABLE IF NOT EXISTS user_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                category TEXT NOT NULL,
                date TEXT,
                content TEXT,
                FOREIGN KEY (username) REFERENCES users (username)
            );
            """
        )  # user_data 테이블 생성 (id, username, category, date, content 포함)


@app.route("/")  # 루트 URL에 대한 라우트
def index():
    if "username" in session:  # 세션에 'username'이 있으면 (로그인된 상태)
        db = get_db()
        cur = db.execute(
            "SELECT category, content FROM user_data WHERE username = ?",
            (session["username"],),
        )
        user_data = cur.fetchall()  # 사용자 데이터 가져오기
        categorized_data = {}  # 카테고리별 데이터 저장을 위한 딕셔너리
        for row in user_data:  # 데이터를 카테고리별로 분류
            if row["category"] not in categorized_data:
                categorized_data[row["category"]] = []
            categorized_data[row["category"]].append(row["content"])
        return render_template(
            "index.html", username=session["username"], user_data=categorized_data
        )  # 데이터를 HTML 템플릿에 전달하여 렌더링
    return render_template("index.html")  # 로그인되지 않았다면 기본 페이지 렌더링


@app.route("/main2")  # /main2 URL에 대한 라우트
def main():
    if "username" not in session:  # 로그인되지 않으면 로그인 페이지로 리디렉션
        return redirect(url_for("index"))

    db = get_db()
    cur = db.execute(
        "SELECT id, category, content, date FROM user_data WHERE username = ?",
        (session["username"],),
    )
    user_data = cur.fetchall()  # 사용자 데이터 가져오기

    user_data_list = [  # 데이터를 평탄화하여 리스트로 변환
        {
            "id": row["id"],
            "category": row["category"],
            "content": row["content"],
            "date": row["date"],
        }
        for row in user_data
    ]

    return render_template(
        "main2.html", username=session["username"], user_data=user_data_list
    )  # 데이터를 HTML 템플릿에 전달하여 렌더링


@app.route("/login", methods=["GET", "POST"])  # /login URL에 대한 라우트 (GET과 POST 요청 처리)
def login():
    if request.method == "GET":  # GET 요청일 때
        return render_template("login.html")  # 로그인 폼을 렌더링
    else:  # POST 요청일 때
        data = request.get_json()  # 클라이언트에서 보낸 JSON 데이터 받기
        username = data.get("username")
        password = data.get("password")

        db = get_db()
        cur = db.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password),
        )
        user = cur.fetchone()  # 사용자 확인
        if user is None:  # 사용자 정보가 없으면 오류 메시지 반환
            return jsonify(
                success=False, message="아이디 또는 비밀번호가 잘못되었습니다."
            )

        session["username"] = username  # 세션에 username 저장
        return jsonify(success=True)  # 로그인 성공 응답


@app.route("/signup", methods=["GET", "POST"])  # /signup URL에 대한 라우트 (회원가입 처리)
def signup():
    if request.method == "GET":  # GET 요청일 때
        return render_template("signup.html")  # 회원가입 폼을 렌더링
    else:  # POST 요청일 때
        data = request.get_json()  # 클라이언트에서 보낸 JSON 데이터 받기
        username = data.get("username")
        password = data.get("password")

        if not username or not password:  # 아이디나 비밀번호가 없으면 오류 메시지 반환
            return jsonify(success=False, message="아이디와 비밀번호를 입력해 주세요.")

        try:
            db = get_db()
            db.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password),
            )
            db.commit()  # 사용자 데이터 삽입
        except sqlite3.IntegrityError:  # 아이디가 이미 존재하면 오류 반환
            return jsonify(success=False, message="이미 존재하는 아이디입니다.")

        return jsonify(success=True)  # 회원가입 성공


@app.route("/main3-2", methods=["GET"])  # /main3-2 URL에 대한 라우트
def main3_2():
    # if "username" not in session:  # 로그인되지 않으면 로그인 페이지로 리디렉션
    #     return redirect(url_for("login"))

    category = request.args.get("category")  # 쿼리 파라미터에서 category 가져오기
    logging.info(f"category: {category}")  # 로그에 카테고리 출력

    return render_template("main3-2.html", category=category)  # 카테고리 데이터를 HTML 템플릿에 전달

@app.route("/update", methods=["GET", "PUT"])
def update():
    if "username" not in session:  # 로그인되지 않으면 로그인 페이지로 리디렉션
        return redirect(url_for("index"))
    
    user_data_id = request.args.get("user_data_id")

    if request.method =="GET":
        db = get_db()
        cur = db.execute(
            "SELECT * FROM user_data WHERE id = ?",
            (user_data_id,),
        )
        user_data = cur.fetchone()  # 사용자 데이터 가져오기
        logging.info(f"user_data: {user_data}")
        return render_template(
            "update.html", 
            category=user_data["category"] if user_data else None, 
            user_data=user_data
        )  # 데이터를 HTML 템플릿에 전달하여 렌더링

    else:
        data = request.get_json()  # 클라이언트에서 보낸 JSON 데이터 받기
        category = data.get("category")
        content = data.get("content")
        date = data.get("date")
        user_data_id = data.get("user_data_id")

        if not category or not content or not date:  # 모든 필드가 입력되지 않으면 오류 반환
            return jsonify(success=False, message="모든 필드를 입력해 주세요.")

        db = get_db()
        db.execute(
            "UPDATE user_data SET username=?, category=?, content=?, date=? WHERE id=?",
            (session["username"], category, content, date, user_data_id),
        )
        db.commit()  # 데이터 저장

        return jsonify(success=True, message="Data updated successfully")  # 성공 메시지 반환
    

@app.route("/save_data", methods=["POST"])  # 데이터를 저장하는 라우트
def save_data():
    # if "username" not in session:  # 로그인되지 않으면 오류 메시지 반환
    #     return jsonify(success=False, message="로그인이 필요합니다.")

    data = request.get_json()  # 클라이언트에서 보낸 JSON 데이터 받기
    category = data.get("category")
    content = data.get("content")
    date = data.get("date")

    if not category or not content or not date:  # 모든 필드가 입력되지 않으면 오류 반환
        return jsonify(success=False, message="모든 필드를 입력해 주세요.")

    db = get_db()
    db.execute(
        "INSERT INTO user_data (username, category, content, date) VALUES (?, ?, ?, ?)",
        (session["username"], category, content, date),
    )
    db.commit()  # 데이터 저장

    return jsonify(success=True, message="Data saved successfully")  # 성공 메시지 반환

@app.route("/delete_data", methods=["POST"])  # 데이터를 삭제하는 라우트
def delete_data():
    # if "username" not in session:  # 로그인되지 않으면 오류 메시지 반환
    #     return jsonify(success=False, message="로그인이 필요합니다.")

    data = request.get_json()  # 클라이언트에서 보낸 JSON 데이터 받기
    entry_id = data.get("id")

    if not entry_id:  # ID가 없으면 오류 반환
        return jsonify(success=False, message="ID를 지정해 주세요.")

    db = get_db()
    db.execute(
        "DELETE FROM user_data WHERE id = ? AND username = ?",
        (entry_id, session["username"]),
    )
    db.commit()  # 데이터 삭제

    return jsonify(success=True, message="삭제되었습니다.")  # 성공 메시지 반환


# @app.route("/logout")  # 로그아웃 라우트
# def logout():
#     session.pop("username", None)  # 세션에서 username 제거
#     return redirect(url_for("login"))  # 홈으로 리디렉션


@app.route("/main3-1", methods=["GET"])  # /main3-1 URL에 대한 라우트
def main3_1():
    if "username" not in session:  # 로그인되지 않으면 홈 페이지로 리디렉션
        return redirect(url_for("index"))

    return render_template("main3-1.html")  # main3-1 템플릿을 렌더링


if __name__ == "__main__":  # 이 파일이 실행될 때
    init_db()  # 데이터베이스 초기화
    app.run(host="0.0.0.0", debug=True, port=5000)  # 앱 실행 (0.0.0.0으로 실행하여 외부 접근 허용)


## 수정 반영 체크