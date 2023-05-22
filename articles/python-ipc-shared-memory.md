---
title: "Pythonでマルチプロセス間で値を共有する仕組み"
emoji: "🌏"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["ipc", "python", "sharedmemory", "linux"]
published: false
---

# 概要
Pythonでは、プロセス間で通信する方法は`multiprocessing.Value`や`multiprocessing.SharedMemory`等がありますが、これらは内部ではどのような実装になっているのでしょうか。本記事では一般的なプロセス間通信の手法がPythonにどのように取り込まれているのかを説明します。


# プロセス間通信について
この章は、プロセス間通信に造詣のある方は飛ばしていただいて構いません。まず**プロセス間通信**とはIPC（inter-process communication）とも呼ばれ、その名の通りプロセス間で値をやりとりすることを指します。プロセス間通信にはいくつかの方法があり、以下のような方法があります。（[こちらの記事](https://qiita.com/n01e0/items/5484dbdc940baa4fde56)で詳しく説明されています。）
- パイプ
- シグナル
- セマフォ
- メッセージキュー
- 共有メモリ
- ソケット

これらはどれもOSのシステムコールを介した方法となっています。マルチプロセス下では、各プロセスごとに独立したメモリ空間がOSによって割り当てられるため、それらの間で通信するにはこのようにOSの機能を用いる必要があります。一方マルチスレッド下においては、メモリ空間は各スレッドで共有されているため、このような方法を使うことなくスレッド間で値を共有できます[^1]。

[^1]: 厳密にはスレッドごとにスタックを持つため、値がヒープ下にあればそのまま共有されます。

このように基本的にはマルチスレッドを使うことで、IPCを使うことなく、より小さなコンテキストスイッチで並列処理が行なえます。しかし、PythonにおいてはGIL（Global Interpreter Lock）という仕組みにより、マルチスレッド下での並列処理は実質的には行なえません。したがってPythonで並列処理を行う際はマルチプロセスを使う必要があり、プロセス間での値の共有には上記のようなIPCの機構を使う必要があります。


# Pythonにおけるプロセス間通信の仕組み
本題です。`multiprocessing.Value`と`multiprocessing.SharedMemory`を各節に分けて順に説明します。


### `multiprocessing.Value`
まず`multiprocessing.Value`を使ったコードを簡単に紹介します。
```python
from multiprocessing import Process, Value

def worker(v: Value):
    with v.get_lock():
        v.value += 1

def main():
    v = Value('i', 0)

    p1 = Process(target=worker, args=(v,))
    p2 = Process(target=worker, args=(v,))

    p1.start(); p2.start()
    p1.join(); p2.join()

    print(v.value)  # supposed to show 2
```
上記コードでは2つのプロセスを生成しており、それらでint型の`Value('i', 0)`を共有しており、各プロセスでその値をインクリメントしています。したがって、この値がIPCのなんらかの機構を用いてこの2つのプロセスで共有されているはずです。

詳細をすっとばして、コードを追っていくと最終的に下の箇所にたどり着きます。
https://github.com/python/cpython/blob/a5f244d627a6815cf2d8ccec836b9b52eb3e8de2/Lib/multiprocessing/heap.py#L67-L90



https://github.com/python/cpython/issues/75102


# 他の言語の
そもそも
