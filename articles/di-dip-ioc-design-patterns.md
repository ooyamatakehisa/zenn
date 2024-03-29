---
title: "DIとDIPとIoCとデザインパターンと"
emoji: "🌏"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["設計", "デザインパターン", "DI", "DIP", "IoC"]
published: true
---

# 概要
本記事では、設計やデザインパターンで頻出の以下の単語の関係性に関する自分の解釈を述べます。

- [依存性の注入 (Dependency Injection: DI)](https://ja.wikipedia.org/wiki/%E4%BE%9D%E5%AD%98%E6%80%A7%E3%81%AE%E6%B3%A8%E5%85%A5)
- [SOLID原則](https://ja.wikipedia.org/wiki/SOLID)
    - [依存性逆転の法則 (Dependency Inversion Principle: DIP)](https://ja.wikipedia.org/wiki/%E4%BE%9D%E5%AD%98%E6%80%A7%E9%80%86%E8%BB%A2%E3%81%AE%E5%8E%9F%E5%89%87)
    - [開放/閉鎖原則 (Open/Closed Principle: OCP)](https://ja.wikipedia.org/wiki/%E9%96%8B%E6%94%BE/%E9%96%89%E9%8E%96%E5%8E%9F%E5%89%87)
- [制御の逆転 (Inversion of Control: IoC)](https://ja.wikipedia.org/wiki/%E5%88%B6%E5%BE%A1%E3%81%AE%E5%8F%8D%E8%BB%A2)
- [デザインパターン](https://ja.wikipedia.org/wiki/%E3%83%87%E3%82%B6%E3%82%A4%E3%83%B3%E3%83%91%E3%82%BF%E3%83%BC%E3%83%B3_(%E3%82%BD%E3%83%95%E3%83%88%E3%82%A6%E3%82%A7%E3%82%A2))
    - [ストラテジーパターン](https://ja.wikipedia.org/wiki/Strategy_%E3%83%91%E3%82%BF%E3%83%BC%E3%83%B3)
    - etc...

自分の中で、この周辺の関連性に関する疑問は頻繁に生じていたため、そういった疑問の解消の手助けになれば幸いです。また本記事におけるデザインパターンとは「オブジェクト指向における再利用のためのデザインパターン」（通称GoF本）という本で定義されたものを指します。

# 単語の関係性
以下の節に分けてそれぞれの関連を説明します。
- DIとDIP
- DIとIoCとデザインパターン
- DIPとOCPとデザインパターン


### DIとDIP
DIPを実現させる方法の一つとしてDIがあります。**依存性の注入（DI）** とは、モジュールAがモジュールBを呼び出している（**依存**している）とき、Aの引数やコンストラクタを介してBを外部からAに渡す（**注入**する）ことを指します。

このときBを受け取るAの引数の型をinterfaceやabstract classなどの抽象型として定義し[^1]、その抽象型を実装したBを注入すれば、AがBに直接依存することを防ぐことができます。つまり、Aは実装の詳細を持つBに依存せず、Bのインターフェースにのみ依存しているということです。また、BはAが定義したBのインターフェースを実装する必要があり、もともとAがBに依存していた関係がDIにより逆転していると言えます。

これはまさに、上位モジュールと下位モジュールはともに抽象に依存するべきで、抽象は詳細に依存してはならないという**依存性逆転の原則（DIP）** を満たしています。まとめると、DIをする際にその依存対象を抽象として扱うことで、DIPを満たすと言えます。

![](/images/di-dip-ioc-design-patterns/di.png =500x)
*図1*
<!-- https://excalidraw.com/#json=ryPQYHAZ6qG7YU-Hsv8RP,TQzqAMsiom4ESleiDyxTvA -->


:::details コード例
- DI前のコード
    ```java
    class A {
        private B b;
        public A(B b) {
            this.b = b;
        }
        public void doSomething() {
            b.doSomething();
        }
    }

    class B {
        public void doSomething() {
            // do something
        }
    }

    class Main {
        public static void main(String[] args) {
            B b = new B();
            A a = new A(b);
            a.doSomething();
        }
    }
    ```

- DIによりDIPを満たすコード
    ```java
    class A {
        private IB b;
        public A(IB b) {
            this.b = b;
        }
        public void doSomething() {
            b.doSomething();
        }
    }

    interface IB {
        public void doSomething();
    }

    class B implements IB {
        public void doSomething() {
            // do something
        }
    }

    class Main {
        public static void main(String[] args) {
            B b = new B();
            A a = new A(b);
            a.doSomething();
        }
    }
    ```
:::

他にDIPを満たすパターンがあるかなと考えたときに、テンプレートメソッドパターンが思い浮かびましたが、「DIPとOCPとデザインパターン」の節で述べる通り、自分の解釈ではDIPは満たしておらず、DI以外にもDIPを満たすパターンがあればコメントいただけると幸いです。

[^1]: 依存対象が関数であればその型を宣言すれば十分ですし、Pythonなどダックタイピングが可能な言語では、抽象型を定義する必要はありません。重要なのは、上位モジュールが下位モジュールの詳細に依存しないことです。


### DIとIoCとデザインパターン
IoCの実現方法としてDIがあります。**制御の反転（IoC）** は、本来プログラマーがmain関数の実行などにより行うプログラムの**制御**を、フレームワークなどプログラマーの実装範囲外が代わりに行ってくれることを指します。例えばフロントエンド開発で、ボタンに対してonClick関数を実装する際、ボタンがクリックされたらその関数を実行するという処理の制御は我々ではなく、あくまでのフレームワーク側もしくはブラウザ側が担ってくれており、これは制御の反転（IoC）だと言えます。
```React
<Button onClick={() => doSomething()}>ボタン</Button>
```


フレームワーク側はボタンが押されたらonClick関数を呼び出すので、onClick関数に依存しています。そして、我々はその依存をcallback関数という形でフレームワーク側に渡します。これはまさに、依存を外部から注入する**DI**であり、DIを用いてIoCを実現していると言えます。

他の例としては、DjangoやExpressなどwebフレームワークも挙げられます。フレームワーク利用者は特定のURLに来たリクエストに対して行う処理のみを実装すればよく、裏で行われているHTTPヘッダーのパースなどに関しては一切行う必要がありません。何らかの形でその処理をフレームワーク側に注入（DI）することで、その処理の呼出をフレームワーク側が自動で行ってくれます（IoC）。

___

またストラテジーパターンもDIにより実現していると言えます。GoFの**ストラテジーパターン**は、再利用したいクラスの中で一部交換可能にしたいアルゴリズムの箇所を抽象クラスとして切り出して定義・使用し、アルゴリズムを実装した詳細クラスは外部から注入することで、オブジェクトを再利用可能にしつつアルゴリズムを交換可能にするパターンです。この詳細アルゴリズムをもつクラスは基本的に再利用したいクラスのコンストラクターを通して外部から注入されるため、ストラテジーパターンは**DI**を使っていると言えます。

アルゴリズムの詳細実装をクラスに制限しなければ、上記のDIの例で挙げた onClick関数やWebフレームワークの例もストラテジーパターンであると解釈できます。onClick関数ではクリックされたときのアルゴリズムを交換可能にしているという意味でストラテジーパターンになります[^5]。またWebフレームワークの例においても、HTTPヘッダーのパースなど共通処理は再利用可能にしつつ、リクエストに対する処理は各ユーザーに対して交換可能にしているという意味でストラテジーパターンと解釈できます。このようにどちらもDIを用いたストラテジーパターンだと言えます。

[^5]: GoF本ではオブジェクト指向の文脈でクラスを用いたストラテジーパターンが説明されていますが、多くのプログラミング言語で関数が第一級オブジェクトとして扱われる現在では、わざわざアルゴリズムをクラスに定義する必要はなく、onClick関数のように関数を直接渡すことで、本質的にストラテジーパターンと同様のことが行なえます。

___

上記の例はReactやDjangoといったフレームワークがDI（ストラテジーパターン）を使ってIoCを実現している例ですが、そもそもフレームワークとはなんでしょうか。自分はフレームワークとライブラリの違いはIoCを実現しているかどうかにあると思っています。つまりフロントエンドやWebに限らず、フレームワークと呼ばれるものは基本的にIoCを実現しており、その実現のためにDIやストラテジーパターンが使われている例は散見されるのではないかと思います。

ただし、IoCの実現方法はDIやストラテジーパターンを使ったものだけではなく、テンプレートメソッドパターンなどの継承を使った方法も考えられます。しかし、継承を用いるオブジェクト間の結合度が高くなるため、基本的にはDIを用いた方法が推奨されます。例えばニューラルネットワークのフレームワークであるpytorchでモデルを定義する際に、`torch.nn.Moodule`を継承して`forward()`メソッドを実装しますが、これはテンプレートメソッドパターンによるIoCと解釈できます。




### DIPとOCPとデザインパターン
DIPを満たすことでOCPも実現されます。

![](/images/di-dip-ioc-design-patterns/di.png =500x)
*図2*

再掲ですが、図2の左図のようにDIPを満たさずモジュールAがモジュールBに直接依存している状況を考えます。
![](/images/di-dip-ioc-design-patterns/dip.png =500x)
*図3*

ここで、上図（図3）のように、AがBの代わりにBと同じインターフェースを持つB'も新たに使いたいという要件があると、Aのコードを変更して条件に応じてBとB'を使い分ける必要が生じます。一方、図3の右図のようにDIPを満たすと、AはBとB'のインターフェースにのみ依存しているため、Aのコードを変更することなく、注入するモジュールBとB'を使い分けることでこの要件に対応することが可能です。これはまさに、モジュールは変更を加えずに拡張ができるべきというSOLID原則の一つである**開放/閉鎖原則（OCP）** を満たしていると言えます。つまりDIPによってOCPが実現されると解釈できます。

___

また、デザインパターンの多くはOCPを満たしています。GoFのデザインパターンは、本の題名に「オブジェクト指向における再利用のための」と入っているように、オブジェクトの再利用が目的の一つです。OCPに従って、オブジェクトが変更せずに拡張可能であれば、直感的にも再利用しやすくなるのは明らかで、OCPを満たしたデザインパターンが多く存在するのも納得できます。

例えば、ストラテジーパターン、オブザーバーパターン、ビルダーパターンなどはDIP原則に従ったデザインパターンであり、したがって上で述べたとおりOCPも満たしたパターンです。他のパターンがどのようにOCPを満たしているかに関して興味がある方は、[こちらの記事](http://objectclub.jp/community/memorial/homepage3.nifty.com/masarl/article/dp-ocp-2.html)が面白いので参考にしてみてください。



:::message
#### テンプレートメソッドパターンはDIPを満たしているか？
テンプレートメソッドパターンは、交換可能にしたいアルゴリズムのメソッドを上位モジュールでアブストラクトメソッドとして定義しておき、そのメソッドを上位モジュールを継承した下位モジュール側で行えば、上位モジュールも下位モジュールも抽象化されたメソッドに依存しておりDIPを実現していると言えそうです。しかし、テンプレートメソッドパターンは下位モジュールが上位モジュールを継承しており、そこには強力な具象への依存が発生しているため、DIPを満たしていないと考えています。
:::

# まとめ
設計周りでよくでてくる単語・デザインパターンの関係をまとめてみました。こういったパターンは繰り返し使われる実装方法を抽象化・言語化しただけなので、（Webフレームワークの例でも見たとおり）実はそこら中で実践されたコードを見つけることができますが、概念を理解していることで設計の手助けになることもあるのかなと思います。

他にも「SOLIDのこの原則とこの原則はこう関係してるよ！」「この関係はこういう解釈のほうがしっくりくる」等々あれば追記いたしますので、コメント等で教えていただけると嬉しいです。


# （付録） DI
DIは本記事でも述べたとおり、DIPやIoCの手段として用いられます。さらにはテスト容易性の向上や結合度の低下にも寄与します。このあたりは[wikipedia](https://ja.wikipedia.org/wiki/%E4%BE%9D%E5%AD%98%E6%80%A7%E3%81%AE%E6%B3%A8%E5%85%A5)にも書いているとおりなのですが、fukabori.fmというPodcastで、グローバルオブジェクト（グローバル変数）の問題を解決するという文脈でのDIという話があり、面白かったので紹介です。また簡単なDIコンテナの実装の話もあり勉強になりました。
https://fukabori.fm/episode/48

