---
title: "DIとDIPとIoCとデザインパターンと"
emoji: "🌏"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["設計", "デザインパターン", "DI", "DIP", "IoC"]
published: false
---

# 概要
本記事では、設計やデザインパターンで頻出の以下の単語たちの関連性をまとめます。

- [依存性の注入 (Dependency Injection: DI)](https://ja.wikipedia.org/wiki/%E4%BE%9D%E5%AD%98%E6%80%A7%E3%81%AE%E6%B3%A8%E5%85%A5)
- [依存性逆転の法則 (Dependency Inversion Principle: DIP)](https://ja.wikipedia.org/wiki/%E4%BE%9D%E5%AD%98%E6%80%A7%E9%80%86%E8%BB%A2%E3%81%AE%E5%8E%9F%E5%89%87)
- [制御の逆転 (Inversion of Control: IoC)](https://ja.wikipedia.org/wiki/%E5%88%B6%E5%BE%A1%E3%81%AE%E5%8F%8D%E8%BB%A2)
- デザインパターン
    - [ストラテジーパターン](https://ja.wikipedia.org/wiki/Strategy_%E3%83%91%E3%82%BF%E3%83%BC%E3%83%B3)
    - [デコレーターパターン](https://ja.wikipedia.org/wiki/Decorator_%E3%83%91%E3%82%BF%E3%83%BC%E3%83%B3)
    - etc...
- [デリゲート（委譲）](https://ja.wikipedia.org/wiki/%E5%A7%94%E8%AD%B2)
- [合成](https://en.wikipedia.org/wiki/Object_composition)

各単語の意味はこの記事では既知とさせていただきます。また本記事におけるデザインパターンとは「オブジェクト指向における再利用のためのデザインパターン」（通称GoF本）という本で定義されたものを指します。

# 単語の関係性
以下の節に分けてそれぞれの関連を説明します。
- DIとDIP
- DIとIoCとストラテジーパターン
- デリゲートと合成とデザインパターンとDI


### DIとDIP
DIPを実現させる方法の一つとしてDIがあります。上位モジュールでコンストラクターの引数の型をinterfaceやabstract classなどの抽象型として定義し、その抽象型にしたがって実装された下位モジュールをコンストラクターに渡してあげれば、上位モジュールが下位モジュールに直接依存することを防ぐことができ、DIによりDIPを実現したということになります。逆にDIをしていれば、DIPを満たすことになります。

ただし、DIPの実現方法はDIだけではありません。DIPは「上位モジュールが下位モジュールに直接依存するな」と言っているだけなので、例えばテンプレートメソッドパターンのように[^1]継承を用いることでも実現可能です。上位モジュールは使用したい下位モジュールのメソッドをアブストラクトメソッドとして定義しておき、それらのメソッドは上位モジュールを継承した下位モジュール側で行えば、上位モジュールも下位モジュールも抽象に依存しておりDIPを実現していると言えます。一方で、DIによるDIPの実現は上位モジュールと下位モジュールの結合度を大きく下げてくれますが、テンプレートメソッドパターンでは継承を用いるため、上位モジュールと下位モジュールの結合度は容易に高くなる可能性があり、推奨される方法ではありません。


[^1]: ここでテンプレートメソッドパターンのようにと書いたのは、テンプレートメソッドパターンはあくまでもアルゴリズムの交換を容易にすることを目的としたパターンであり、DIPのためのパターンではないからです。しかしアブストラクトメソッドを継承先に実装させて、親クラスでそれを使うという構造は同じです。

:::message
#### DIのメリットとデメリット
メリット
- テスト容易性
- 結合度の低下
- DIPの実現
- グローバルオブジェクトを削除し、オブジェクトへの依存をコントロールできる（付録「DI」で説明）

デメリット
- DIコンテナなしではオブジェクトの初期化が複雑
:::


### DIとIoCとストラテジーパターン
IoCの実現方法としてDIがあります。この方式は得に意識しませんがあらゆるところにあると思います。例えばフロントエンドを書くときに、ボタンに対してonClick関数を実装することはよくありますが、ボタンが押されたらユーザーの処理を実行するという処理の制御は我々ではなく、あくまでのフレームワーク側もしくはブラウザ側が担ってくれており、これは制御の反転（IoC）だと言えます[^2]。フレームワーク側はボタンが押されたらonClick関数を呼び出すのでonClick関数に依存しており、それがcallback関数という形でフレームワーク側に注入されているという意味でDIによりIoCを実現していると言えます。他には多くのwebフレームワークにおいて、フレームワーク利用者は特定のURLに来たリクエストに対して行う処理を実装しますが、何らかの形でその処理をフレームワーク側に注入（DI）することで、その処理の呼出をフレームワーク側が自動で行ってくれます（IoC）。


[^2]: フレームワークとライブラリの違いは、IoCが実現されているかどうかにあると思うので、循環論法的な説明になっています...

またストラテジーパターンもDIにより実現していると言えます。GoFのストラテジーパターンは、主な処理のフローを担うクラスAにアルゴリズムの詳細をもつ別クラスBをメンバーとしてもたせることで実現しますが、この詳細クラスBも基本的に外部から注入されるという点でDIを使っていると言えます。このアルゴリズムの詳細実装をクラスに制限しなければ、上記のonClick関数の例も、onClickされたときのアルゴリズムを交換可能にしているという意味でストラテジーパターンになります。このようにストラテジーパターンはIoCの実現方法にもなりえます。DIを使うデザインパターンは他にも多数存在します。

フレームワークを実装するというのはIoCを実現することであり、そのためにDIは自ずと使われるもので、その実はストラテジーパターンになっているということが多いのではないかなと思います。


### デリゲートと合成とデザインパターンとDI

:::message
#### デリゲートとは
デリゲート（委譲）はいくつかの意味が混在して使われますが、本記事では「あるオブジェクト（Wrapper）のメンバーから、そのオブジェクトのメンバーである別オブジェクト（Wrappee）のメンバーが呼ばれる」という意味でデリゲートという単語を使用します。正確には「デリゲート」はWrappeeのメンバーの評価がWrapper側で行われる場合のことを指しており、本記事で使用する「デリゲート」では、Wrappeeのメンバーの評価がWrappee側で行われるため、正確には「**フォワーディング（転送）**」と呼ばれます[^3]。


[^3]: 英語版のwikipediaには[forwarding](https://en.wikipedia.org/wiki/Forwarding_(object-oriented_programming))のページがあり、デリゲートとの違いが述べられています。日本語版では[委譲](https://ja.wikipedia.org/wiki/%E5%A7%94%E8%AD%B2)のページでフォワーディングが（誤って？）説明されています。

なお、英語版wikipediaの[forwarding](https://en.wikipedia.org/wiki/Forwarding_(object-oriented_programming))のページでは、WrapperとWrappeeのメンバーは1:1対応し、同じ責務を持つ（同じインターフェースを実装している）ことも定義の一部となっているようですが、本記事ではこの定義を「**狭義のフォワーディング**」として言及し、デリゲートは単純にWrapperからWrappeeのメンバーが呼ばれていれば良いものとします。これに関しては「（付録）狭義のフォワーディング」で追記します。


フォワーディングはクラスに限った話ではなく、例えばあるメソッドが内部で別のメソッドを呼んでいてもフォワーディングと呼びます[^4]。継承して子クラスのメソッドから親クラスのメソッドを呼ぶ場合でもフォワーディングの定義は満たしています。
:::


デリゲートは合成の必要条件です。合成は合成されたクラスのメンバーを使うことが目的なので、合成をするなら多くの場合デリゲートをしていることになります。ただし、デリゲートは「クラスのメソッドからそのクラスのメンバーである別クラスのメソッドを呼ぶこと」というオブジェクト指向の文脈で使われることが多く、この文脈では合成はデリゲートの前提となっています。

![](/images/di-dip-ioc-design-patterns/delegate.png =350x)

[^4]: wikipediaの[forwarding](https://en.wikipedia.org/wiki/Forwarding_(object-oriented_programming))のページには、フォワーディングとデリゲートを説明するために、クラスではなくメソッドにおける例が紹介されています。


合成によるデリゲートを使ったデザインパターンは色々あります。ストラテジーパターン・デコレーターパターン・オブザーバーパターン・プロキシパターンなどは、まさにDI・合成・デリゲートを用いたパターンです。特にデコレーターパターンやプロキシパターンではWrapperとWrappeeは同じインターフェースを実装しておりメンバーは1:1対応しているため、これは狭義のフォワーディングといえます。



# まとめ
設計周りでよくでてくる単語・デザインパターンの関係をまとめてみました。こういったパターンは繰り返し使われる実装方法を抽象化・言語化しただけなので、そのものは難しくないですが、概念を理解していることで設計の手助けになることもあるのかなと思います。


# （付録） DI
DIは本記事でも述べたとおり、DIPやIoCの手段として用いられます。さらにはテスト容易性の向上や結合度の低下にも寄与します。このあたりは[wikipedia](https://ja.wikipedia.org/wiki/%E4%BE%9D%E5%AD%98%E6%80%A7%E3%81%AE%E6%B3%A8%E5%85%A5)にも書いているとおりなのですが、t_wadaさんがゲスト回のfukabori.fmで、グローバルオブジェクトの問題を解決するためのDIという話があり、面白かったので紹介です。また簡単なDIコンテナの実装の話もあり勉強になりました。
https://fukabori.fm/episode/48

# （付録）開放/閉鎖原則とデザインパターン
本記事ではSOLID原則のDである依存性逆転の法則とデザインパターンの関連を説明しました。以下の記事では、SOLID原則のOである開放/閉鎖原則とデザインパターンの関連を説明してあり非常に面白いです。

http://objectclub.jp/community/memorial/homepage3.nifty.com/masarl/article/dp-ocp-2.html


# （付録）狭義のフォワーディング

英語版のwikipediaにおける[forwarding](https://en.wikipedia.org/wiki/Forwarding_(object-oriented_programming))の定義は、
>forwarding means that using a member of an object (略) results in actually using the **corresponding** member of a different object

> （訳）ファワーディングは、あるオブジェクトのメンバーを呼ぶと、別オブジェクトの**対応する**メンバーが呼ばれることである

となっています。「対応する」の意味が曖昧なのですが、これは「同じ責務を持つ」ということを意味するのかなと思います。別の言い方をすると、WrapperとWrappeeが同じインターフェースを実装しているということになります。

wikipediaに載っている例は基本的にWrapperとWrappeeのメンバーは同じメソッドを持っており、例として挙げられてるデザインパターンもデコレーターパターンやプロキシパターンなどのWrapperとWrappeeが同じインターフェースを実装しているものばかりのため、wikipediaにおけるフォワーディングの定義は、このようにWrapperとWrappeeのメンバーが1:1対応していることが前提なのかなと思います。つまり、この定義ではある処理の流れの中で合成されたオブジェクトのメンバーを呼ぶこと、例えばストラテジーパターンなどは、フォワーディングとは呼ばないのかなと思います。

論文でのフォワーディングの定義は見つけられなかったのですが、デリゲートに関する論文の以下のような記載から、やはりフォワーディングはWrapperとWrappeeのメンバーが対応していることは前提としているのかなと思います。

>  If the object's personal characteristics are not relevant for answering the message, the object forwards the message on to the prototypes to see if one can respond to the message. This process of forwarding is called delegating the massage.
https://dl.acm.org/doi/pdf/10.1145/28697.28718

> Delegation, as discussed by Lieberman in [1] for a class-free (prototype-based) object model, is originally understood as the automatically forwarding of messages for which the receiving object (the message receiver) has no matching methods to a so-called parent object.
https://www.researchgate.net/profile/Bo-Jorgensen-5/publication/220901454_Superimposed_Delegation/links/0046351ca8d7de2062000000/Superimposed-Delegation.pdf

