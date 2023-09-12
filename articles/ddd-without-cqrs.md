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
- 不必要なデータまで取得する必要がある
- 複数リポジトリからとってきた集約を組み合わせてクライントのためにDTOの詰め替えを行う必要がある
- そもそもドメインロジックを使わない

以下で実例を通して上記のような問題が起こる原因を解説していきます。

# 題材
本記事を通して使用する題材を紹介します。
![](https://storage.googleapis.com/zenn-user-upload/36fc66d6b502-20221122.png)
今回は学校の部活管理システムを構築することとし、上図のように部活`Club`と生徒`Student`を考えます。部活は複数の生徒を持ちますが、生徒が一人もいなくても成立するものとします。学生は部活に入らなくてもいいですが、入る場合は複数の部活には入れないものとします。

DBには以下のような`clubs`テーブルと`students`テーブルがあるものとします。部活と生徒の関係は1:nなので、各生徒がどの部活に所属しているかの情報は`students`テーブルに`club_id`というカラムで保存します。

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

# DDDにおける実装
本章では、上記の題材に対するDDDのドメインモデル・リポジトリ・アプリケーションサービスの実装を説明します。ドメイン駆動設計(DDD)の簡単な説明と。DDDをご存じの方はこの章は飛ばして[次の章](#CQRSを使用しないDDDの問題点)を御覧ください。
:::message alert
下記の実装は、本記事の趣旨を説明するために簡素化したものであり、実用を意識したものではないのでご注意ください。例えば、各idには固有の型をもたせてタイプセーフにするべきですし、アプリケーションサービスも各ユースケースごとにクラスを分割し凝集度をあげるべきです。
:::


### ドメインモデル
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
本記事では部活動`Club`と生徒`Student`は別集約とし、`Club`は生徒のIDのリストを持つこととします。

:::details ドメインモデルとは
DDDでは開発を行うソフトウェアの対象領域（ドメイン）の実体をクラス等に落とし込み、その振る舞いを表現します。今回は、学校の部活管理システムを構築するので、各部活動や生徒といった現実世界の実体をそのまま上記コードのようなクラスに落とし込みます。

クラスに「振る舞いを表現する」というのは、例えば上記では以下のようなことを指します。
- ある学生が部活に入部することを`join`メソッドで表現
- 部活には人数の上限があることを`join`メソッドのif文チェックで表現

このように対象領域（ドメイン）の実体を落とし込んだクラス等のことを**ドメインモデル**といいます。部活に人が入る入部という振る舞いや部活の人数制限といった、ドメインのルールや制約をモデルにまとめて表現することで、（データの保存方法やデータのリクエスト方法などに依存しない）ドメインの知識が他レイヤーなどに流出することが防げます。また、この`Club`クラスのコードを読めば部活の人数の制限がわかるように、自身がドメインのドキュメント的な意味合いももち、保守性や可読性も高まります。さらに、Javaなどのメンバ変数をprivateにできる言語を使う際は、`student_ids`をprivateなフィールドにすることで`student_ids`を外部から操作されることを防ぐことができ、このフィールを操作できるのはあくまでも「入部」と「退部」に対応する`join`と`leave`メソッドに限定することができます。一般的に、フィールドはprivateにして、ドメインモデルの状態は変更はそこに記述された振る舞いに限定することが推奨されます。

### 値オブジェクトとエンティティ
ドメインモデルには値オブジェクトとエンティティがあります。
**値オブジェクト**は`int`型や`string`型のようにその値が意味を持ち、値が変われば別のものとみなされるものを扱うモデルです。クラスにおいて、ここでの「値」は各フィールドを表します。例えば`host`フィールドと`domain`フィールドを持つ`Email`クラスを考えると、これはいずれかのフィールドが別の値を持てば別のメールアドレスとみなされます。このように、モデルの持つ値のみに関心がある場合は値オブジェクトとして実装します。このような性質上、値オブジェクトのインスタンスの等価性は各フィールドの比較により行うことができます。
また、値オブジェクトはフィールドの値が変われば別の実体を表すため、「状態」を持ちません。例えば、人をモデル化すると身長や体重などの変化しうる状態を持ちますが、その状態が変わってもそのモデルが表す実体は変わりません。（Aさんの背が伸びても、Aさんであることは変わらないように）を上記コードの`Club`クラスの`join()`メソッドのような、値オブジェクトは自身のフィールドの値を変更する操作は持ちません。したがって値オブジェクトはイミュータブルオブジェクトとして実装することが多いです。ちなみに値オブジェクトはDDD以外の文脈でも使用されますが、微妙に定義は異なっています。[こちらの記事](https://blog.j5ik2o.me/entry/2022/05/22/204535)がそのあたりについて詳しく説明されています。

**エンティティ**は、値オブジェクトとは逆で、クラスのフィールで等価性の比較が行えずライフサイクルを持つ実体を扱うモデルです。例えば本記事の`Club`インスタンスは、新たに生徒が入部し`student_ids`フィードのリストの値が変わっても依然として同じ実体を表します。また、`name`フィールが「蹴球部」から「サッカー部」にかわったとしても同じ実体を表しています。このようにエンティティはライフサイクルを持つような実体を扱うモデルです。フィールドは可変であるため、等価性はそのフィールドの比較では行えず、一般的に各エンティティに発行される識別子(ID)で比較されます。
:::

:::details 集約とは

:::



### リポジトリ
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
```

:::details リポジトリとは
リポジトリではドメインモデルが扱わなかったデータの取得や永続化といった処理を行います。ドメインモデルのメソッドは自身のインスタンスの状態を変更しますが、その結果をDB等に永続化するのがリポジトリの役割です。またDB等に永続されたデータからある状態を持つドメインモデルの取得を行うのもリポジトリの役割です。


上記コードにおいて、`get`メソッドは`club_id`を持つ`Club`の取得、`save`メソッドがは`Club`インスタンスの永続化を行っています。

リポジトリは永続化を行うための実装の詳細は隠蔽し、アプリケーションサービスやドメインモデルからはメモリ上のリストからインスタンスを取得するようなインターフェスを提供することが望ましいです。これにより、ドメインロジックはデータの読み書きを意識する必要がなくなります。またこれは採用するアーキテクチャーによりますが、Clean ArchitectureなどSOLID原則における **依存性逆転の原則(DIP)** に準拠したアーキテクチャの場合はこのレイヤーの交換も容易になります。

:::

###  アプリケーションサービス
```Python

class ClubApplicationService:
    def __init__(self, club_repository):
        self.club_repository = club_repository

    def get(self, club_id) -> Optional[Club]:
        return self.club_repository.get(club_id)

    def join(self, club_id, student_id):
        club = self.club_repository.get(club_id)
        if club is None:
            raise Exception("部活が存在しません")

        club.join(student_id)
        self.club_repository.save(club)

    def leave(self, club_id, student_id):
        pass
```


:::details アプリケーションサービスとは
ドメインモデルやリポジトリを使ってアプリを操作する部分です。このあたりをよく「ビジネスロジック」と言ったりします。
:::



:::details CQRS
:::

# CQRSを使用しないDDDの問題点

### N+1問題が発生しやすい
部活名に「球」が入っている部活一覧を取得したいとします。

逆にいうと複雑なクエリを書かないと一発でとってこれない
正規化されているせい？


### 不必要なデータまで取得する必要がある
クライアントで部活名に「球」が入っている部活名一覧を取得したいとします。この時クライアントが必要としているデータは部活名一覧のみで、各部活にどの生徒が所属しているかという情報は必要ありません。しかしDDDの原則に従えば、リポジトリの返り値は集約単位であるため、このようなケースでも生徒のidをDBから取得し`student_ids`をフィールドとして持つ`Club`モデルとしてアプリケーションサービスに返す必要があります。

さらにここで問題なのが集約単位のデータをとってくる際にJOINのようなDBの重い操作が介在している点です。もし各部活に1万人の生徒が所属していたとすると、クライアントが必要としているデータは部活名一覧のみであるにもかかわらず、DBからは「部活数 x 1万人」の生徒のidを取得する必要があります。このようなケースでは、クライアントが必要としているデータ以外のデータを取得する必要があり、不必要なデータを取得する必要があります。

このように、**DDDでの取得処理は、リポジトリの返り値の単位が集約であることが原因で余計なデータの取得を伴うことが多く、さらにその取得のためにパフォーマンスが悪化することがあります。**

