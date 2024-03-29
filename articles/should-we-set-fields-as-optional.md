---
title: "WebアプリケーションのAPIのフィールドはOptionalにすべきか？"
emoji: "🌏"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["graphql", "grpc", "rest", "openapi", "protobuf"]
published: true
---

# 概要
先日、GraphQLのスキーマを作成しているときに、リクエスト・レスポンスのフィールドはすべてoptionalにすべきだというご指摘をうけました。

WebアプリケーションにおけるAPIの種類は、GraphQL / gRPC / RESTなど様々なものがありますが、GraphQLやOpenAPIでは、リクエスト内のフィールドが必ず指定されるべきか（required / non-nullable）、または指定されていなくてもいいか（optional / nullable）をスキーマ上で表現することができます。ここで、gRPCを除いたのはgRPCで使用するProtocol Bufferのバージョン3から、requiredが廃止されているためです。

この記事では、Protocol Bufferの仕様変更のように、WebアプリケーションのAPIのフィールドはrequiredは極力避けてoptionalにすべきか？という問題について考えていきます。

# 前提
本記事で言及するoptionalとrequiredは、あくまでもAPIスキーマ上での定義と、それに伴うプロトコル上でのバリデーションの話であり、ビジネスロジックの実行に各フィールドが必要な場合のコード上でのバリデーションとは分けて考えます。仮にAPIのリクエストフィールドにrequiredを一切使わないという選択をした場合でもビジネスロジックで必要なバリデーションは別途コード上で実装する必要があります。

また本記事では以下の二つのケースを区別せず、同様のものとして扱います。
- あるフィールドがリクエストまたはレスポンスに存在しない
- あるフィールドがリクエストまたはレスポンスに存在するがnullが指定されている


# Protocol Bufferのrequiredが廃止された理由
まずは、gRPCで使用されているProtocol Bufferでrequiredが廃止された理由を見ていきます。
https://github.com/protocolbuffers/protobuf/issues/2497
https://capnproto.org/faq.html#how-do-i-make-a-field-required-like-in-protocol-buffers
ここに理由が記載されています。

簡単に要約すると、（gRPCではなく）メッセージングでProtocol Bufferを使用している際に、あるメッセージプロバイダーが特定のrequiredフィールドが必要無くなったことに気づき、そのフィールドをoptionalに変更するため、コンシューマーにはその対応をあらかじめしてもらい、不必要になったメッセージの送信をやめたところ、メッセージングバス自体は古いprotobufを使用したビルドのままであったため、メッセージのプロバイダーとコンシューマーだけでなく、メッセージングバスを使用しているあらゆるシステムでエラーが発生した。Googleでは、同様のエラーが頻発していて、メッセージの内容に関心のないプロトコルレベルでこのようなバリデーションはするべきではなく、アプリケーションのロジックでするべきだ。とのことです。


つまりここで述べられている理由は、**メッセージングでProtocol Bufferを使っていた際に、requiredがあることで互換性を保たない変更ができてしまい、その結果意図しないエラーが発生しうるため**、ということです。WEBアプリケーションのAPIでも同様の問題は起こり、例えばサーバー側であるrequiredフィールドをすべてのクライアントに伝えることなく追加した場合、そのクライアントはそのフィールドを指定しないため、サーバー側でエラーが発生します。

では、APIにおいても常にリクエストのフィールドはoptionalにすべきでしょうか。例えば、マイクロサービスアーキテクチャにおいて、あるサービスのクライアントが多数あるという状況においては同様の問題を避けるため、すべてoptionalにするという選択は妥当かもしれません[^1]。

[^1]: マイクロサービス間の通信にはgRPCを使用することが多いと思うので、Protocol Buffer3を使用している場合は、上述の通りrequiredは使用できないため、この問題は発生しません。

# requiredによるその他の問題
上記のProtocol Bufferの問題と近いですが、requiredを使用することでAPIの変化を難しくするという主張もあります。

実際に、requiredに伴った以下の変更では互換性が保証されないため、クライアントの事前の対応が必要になります。
1. リクエストにrequiredフィールドを追加
1. リクエストのoptionalフィールドをrequiredに変更
1. レスポンスのrequiredフィールドを削除
1. レスポンスのrequiredフィールドをoptionalに変更

例えば、突然サーバー側が一つ目の変更を行うと、クライアントは新たに追加されたrequiredフィールドを含めずにリクエストを送っているためサーバー側はエラーを返し、そのクライアントは意図しないエラーに遭遇することとなります。こういった問題をさけるために、クライアントはあらかじめサーバー側の変更に対応できるような修正を加える必要があります。クライアントが相当数ある場合、全クライアントの対応を待つ必要があり、上記のようなサーバーの変更をデプロイするためには一定の時間がかかります。また、クライアントが一般ユーザーであるようなパブリックなAPIの場合は、このような変更は基本的に難しくなります。

----
しかし、上記のような変更はそもそも本当に発生するのでしょうか。また、requiredの使用を避けることで上記の問題は解決するのでしょうか。

まず一つ目の「リクエストにrequiredフィールドを追加」の変更は基本的にあまり行われないように感じます。最終的にrequiredにしたいような重要なフィールドを追加する際においても、まずは新規フィールドをoptionalとして追加しクライアントの移行が完了したタイミングで二つ目の「リクエストのoptionalフィールドをrequiredに変更」が行われるのが一般的だと思います。これらのrequiredフィールドの追加は・変更は、基本的にビジネスロジックにおいてもそのフィールドが必要になるということと同義であり、仮にrequiredがスキーマで使えない仕様であっても、実際にそのフィールドがリクエストに存在しない場合はビジネスロジック上でエラーを返すことになり、クライアントの対応を待つ必要があるのは変わりません。つまり **「リクエストにrequiredフィールドを追加」と「リクエストのoptionalフィールドをrequiredに変更」の二つのケースでは、APIスキーマのrequiredの有無に関わらずクライアントの対応を待つ必要があり、requiredがあることでAPIの変更が難しくなるとは言えません**。

三つ目と四つ目の「レスポンスのrequiredフィールドを削除」と「レスポンスのrequiredフィールドをoptionalに変更」が起こるケースとしては、あるレスポンスのフィールドをdeprecatedにする場合が考えられます。このケースでは、requiredが存在せず全てのフィールドをoptionalとするという選択をしていれば、クライアントは初めからフィールドがnullの場合に対応するコードを書く必要があり、サーバー側はクライアントの対応を待たずにフィールドの削除等を行うことが可能となります。つまり **「レスポンスのrequiredフィールドを削除」と「レスポンスのrequiredフィールドをoptionalに変更」の二つのケースでは、全てのフィールドをoptionalとして定義することで、APIの変更が容易になり、逆にrequiredの使用で難しくなると言えます**。一方で、requiredの使用を避けるということは次章で述べる問題もあり注意が必要です。また、requiredなフィールドを削除もしくはoptionalに変更するというタスクは、基本的にそこまで優先順位が高くなく、変化の速度を求められるような変更ではない可能性が高いため、時間がかかっても最終的にクライアントの対応が可能なのであればrequiredの使用は問題ないとも考えられます[^2]。


[^2]: 一般的には、ある変更を簡単にデプロイできないというのは、その変更に依存する後続の変更が全てデプロイできないことを意味し、避けられるべきです。実際にデプロイ頻度がビジネスの成長に影響を与えることも証明されています。



# requiredを使わない場合の問題
requiredを廃止し全フィールドがoptionalの場合、APIクライアントのユーザービリティが低下するという問題もあります。

リクエストに関しては、クライアントはスキーマ自身からはどのフィールドが本当に必要かどうか分からず、実際にリクエストを送りそのレスポンスにエラーがないことを確認してはじめてその要否がわかります。もちろん全てのフィールドに対して、各フィールドがビジネスロジック上で必要かどうかのコメント（ドキュメント）があれば問題ありませんが、実際それが省かれてしまうのは少なくないと感じます。

レスポンスに関しては、コメントがなければ、各フィールドが実際には常に返されるフィールドかどうかはサーバー側のコードを読まないと分からず、クライアントは全てのフィールドがnullになりうるという仮定のもとでコードを書く必要があります。これは、実際には常に値が存在するフィールドに対しても余計なnullチェックを実装する必要があるということを意味します。optionalなフィールドはクライアントのビジネスロジックにまで影響し、クライアントのコードが複雑になるのは明らかです。これらの問題は、クライアントが身内であれば軽減される可能性がありますが、クライアントが一般ユーザーでや別のチームである場合に、クライアントの開発効率に大きな悪影響を及ぼします。

:::message
コメントが書かれていたとしても、それはコメントとコード上の二箇所に制約が現れているという点でDRY原則に反しており、例えばコードのバリデーションロジックは更新されてもコメントは更新されていないというような問題をはらみます。
:::

適切にビジネスロジックを反映したモデリングをAPIスキーマにも行うという意味で、requiredとoptionalを使い分けるのは、クライアントに対してよりわかりやすいインターフェースを提供することにつながり、APIの理解という点でもrequiredを使用するのは合理的だと感じます。

optionalとrequiredを使い分けても、入力文字列の長さの制限など全ての制約がスキーマ上で表現できるわけではなく、別途サーバーのコード上で行われるバリデーションは必ず存在し、クライアントに暗黙的に存在する制約は常に考えられます。しかし、**DRY原則を満たしつつ、クライアントに理解しやすい形でスキーマとしてその制約が表現されていることは、依然として有益だと考えます**。


# 結論
結論としては、一つのスキーマが多くのクライアントで使用されているような場合は、Protocol Bufferの変更のように、requiredの使用は避けるべきです。それ以外の場合では、リクエストに関しては基本的にrequiredを使用して問題ないと考えます。レスポンスに関しては、クライアントの対応を強制するのが難しいパブリックなAPI等ではrequiredの使用は避け、逆に社内専用などの、一定の時間がかかったとしてクライアントの対応が保証できるようなAPIでは、requiredを使用して問題ないと考えます。もちろん、パブリックなAPIでも必ず変更されないと保証されるフィールドに対してrequiredを採用することは妥当な選択だと思います。



# 参考
https://medium.com/@calebmer/when-to-use-graphql-non-null-fields-4059337f6fc8
https://stackoverflow.com/questions/31801257/why-required-and-optional-is-removed-in-protocol-buffers-3
https://www.apollographql.com/blog/graphql/basics/using-nullability-in-graphql/