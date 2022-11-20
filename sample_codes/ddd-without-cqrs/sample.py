from typing import Optional

MAX_NUM_MEMBER = 20

# 部活
class Club:
    def __init__(self, id, name, students_ids):
        self.id = id
        self.name = name                 # 部活名
        self.student_ids = students_ids  # 部活に所属している生徒のID

    # 入部
    def join(self, student_id):
        if len(self.student_ids) > MAX_NUM_MEMBER:
            raise RuntimeError(f"部活の人数は{MAX_NUM_MEMBER}人までです")

        self.student_ids.add(student_id)

    # 退部
    def leave(self, student_id):
        if student_id not in self.student_ids:
            raise RuntimeError(f"{student_id}は部活に参加していません")

        self.student_ids.remove(student_id)


# 生徒
class Student:
    def __init__(self, id, name):
        self.id = id
        self.name = name


class ClubRepository:
    def __init__(self, db):
        self.db = db

    # club_idに対応するClubのドメインモデルを取得する
    def get(self, club_id) -> Optional[Club]:
        query = (
            "SELECT clubs.id, clubs.name, students.id "
            "FROM clubs "
            "LEFT JOIN students "
            "ON clubs.id = students.club_id "
            "WHERE clubs.id = %s"
        )
        with self.db.cursor() as cursor:
            cursor.execute(query, (club_id,))

            rows = list(cursor.fetchall())
            if len(rows) == 0:
                return None

            student_ids = []
            for (club_id, club_name, student_id) in rows:
                student_ids.append(student_id)

        return Club(id=club_id, name=club_name, student_ids=student_ids)

    # ClubのドメインモデルをDBに永続化する
    def save(self, club):
        old_club = self.get(club.id)
        with self.db.cursor() as cursor:
            query = (
                "INSERT INTO clubs "
                "VALUES (%s, %s) "
                "ON DUPLICATE KEY UPDATE name=%s"
            )
            cursor.execute(query, (club.id, club.name, club.name))

            query = (
                "UPDATE students "
                "SET club_id=%s "
                "WHERE student_id in (" + ",".join(["%s"] * len(club.student_ids)) + ")"
            )
            cursor.execute(query, tuple(old_club.student_ids))

            cursor.commit()
