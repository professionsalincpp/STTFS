# Structure

simple file system

```
folder "src" () {
    file "test.h" (encoding="UTF-8", replaceifexists=false)
    %
    #pragma once
    #include <stdio.h>

    void test() {
        printf("Hello World!");
    }
    %
    for [i=0;i<10;i++] {
        file "test${i}.cpp" (encoding="UTF-8") 
        %
        #include "test.h"

        void test() {
            printf("Hello World!");
        }
        %
    }
    file "main.cpp" (encoding="UTF-8")
    %
    #include "test.h"

    int main() {
        test();
    }
    %
}

```