---
title: "なぜDDDにはCQRSが必須なのか"
emoji: "🌏"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["ddd", "cqrs", "python"]
published: false
---

# 概要
DDDの解説記事はよくあるのですが、DDDにCQRSを導入しなかったことによる苦労まで言及した記事があまり見当たらなかったため、簡単なDDDとCQRSの説明と実例を通して、CQRSを使わないDDDの問題点を紹介します。以下が問題点一覧です。
- N+1問題が発生しやすい
- リポジトリの返り値は集約単位であるため、不必要なデータの取得が必要
- 複数リポジトリからとってきた集約を組み合わせてクライントのためにDTOの詰め替えを行う必要がある
- そもそもドメインロジックを使わない

以下で実例を通して上記のような問題が起こる原因を解説していきます。

# DDD
本章ではドメイン駆動設計(DDD)の説明を簡単に行います。DDDをご存じの方はこの章は飛ばして[次の章](#CQRSを使用しないDDDの問題点)

:::details ドメインモデル
DDDでは開発を行うソフトウェアの対象領域（ドメイン）の実体をオブジェクト指向のようにクラス等に落とし込み、その振る舞いを表現します。例えば学校の部活管理システムを構築する際、各部活動や生徒といった現実世界の実体をそのまま以下のようなクラスに落とし込みます。
```Python
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

```
クラスに「振る舞いを表現する」というのは、例えば上記では以下のようなことを指します。
- ある学生が部活に入部することを`join`メソッドで表現
- 部活には人数の上限があることを`join`メソッドのif文チェックで表現

このように対象領域(ドメイン)の実体を落とし込んだクラス等のことを**ドメインモデル**といいます[^1]。部活に人が入る入部という振る舞いや部活の人数制限といった、ドメインのルールや制約をモデルにまとめて表現することで、（データの保存方法やデータのリクエスト方法などに依存しない）ドメインの知識が他レイヤーなどに流出することが防げます。また、この`Club`クラスのコードを読めば部活の人数の制限がわかるように、自身がドメインのドキュメント的な意味合いももち、保守性や可読性も高まります。Pythonでは難しいですが、他の言語では`student_ids`をprivateなフィールドにすることで`student_ids`を外部から操作されることを防ぐことができ、このフィールを操作できるのはあくまでも「入部」と「退部」に対応する`join`と`leave`メソッドに限定することができます。フィールドをprivateにすることでドメインモデルの状態を変更するのはそこに記述された振る舞いに限定することができます。

[^1]: ドメインモデルには値オブジェクトとエンティティがありますが、ここでは割愛します。
:::

:::details リポジトリ
リポジトリではドメインモデルが扱わなかったデータの取得や永続化といった処理を行います。ドメインモデルのメソッドは自身のインスタンスの状態を変更しますが、その結果をDB等に永続化するのがリポジトリの役割です。またDB等に永続されたデータからある状態を持つドメインモデルの取得を行うのもリポジトリの役割です。

ではドメインモデルの説明でとりあげた`Club`と`Student`の例をもとにリポジトリの具体例を以下で説明します。今回は簡単のため、各生徒は兼部はできないという設定にし、`Club`と`Student`は1:nの関係とします。DBには以下のような`clubs`テーブルと`students`テーブルがあるとします。

- clubsテーブル

	| id | name |
	| ---- | ---- |
	| club_id1 | 野球部 |
	| club_id2 | 軽音部 |

- studentsテーブル
	| id | name | club_id |
	| ---- | ---- | ---- |
	| student_id1 | 大谷翔平  | club_id1 |
	| student_id2 | ヴァン・ヘイレン | club_id2 |
	| student_id3 | 平沢唯 | club_id2 |

このとき、リポジトリの実装は以下のようになります。


```Python
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
            for (club_id, club_name, student_id) in :
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

```
上記リポジトリでは`get`メソッドである`club_id`を持つ`Club`の取得、`save`メソッドである`Club`インスタンスの永続化を行っています。

:::


### アプリケーションサービス
ここで上記の

# CQRSを使用しないDDDの問題点

