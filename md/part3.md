> 구현한 항목뿐만 아니라, 전체 프로그램 코드의 동작에 대해 설명

### `int main(int argc, char* argv[])` - 메인 함수

먼저 메인 함수에서 호출하는 함수들을 알아보자.

1. `signal` : 커스텀 시그널 핸들러를 등록한다. 시그널 함수에 대한 자세한 설명은 밑의 추가 고찰에서 다루도록 한다. 해당 프로그램에서는 키보드에 의한 인터럽트를 핸들링한다.
2. `srand` : 시간을 통해서 시드를 초기화 한다. 해당 함수를 통해서 rand() 함수를 사용할 때 마다 랜덤한 값을 얻을 수 있다.
3. `calculatePageInfo` : 입력 정보(페이지 오프셋)을 통해서 페이지 크기 및 페이지 개수를 계산한다. 이 함수를 통해서 전역 변수 page_size 및 num_pages에 대해 값의 할당이 이루어진다. `./a.out 13 d` 커멘드를 통해서 실행하게 되면 page_bits는 13이 되는데, 다음과 같이 값이 정해진다

```c
#define ADDR_SIZE 27 //주어진 시스템은 27-bit 주소를 사용함

void calculatePageInfo(int page_bits) {
    page_size = 1 << page_bits;
    num_pages = 1 << (ADDR_SIZE - page_bits);
}
```

- **입력한 페이지 별 크기** : `page_size` = 8192Bytes = **2^13**
- **프로세스의 페이지 개수** : `num_pages` = 16384개 = **2^14**

여기서 중요한 핵심 포인트는 **입력한 페이지 별 크기 \* 프로세스의 페이지 개수**는 항상 **2^27**이 된다는 것이다. 매서드로 정의된 ADDR_SIZE의 값이 27인 것을 통해서 페이지 크기를 키우면 페이지의 개수를 줄어든다는 것을 알 수 있다.

1.  **페이지 테이블 할당 및 초기화**

```c
pageTable = (int*)malloc(num_pages * sizeof(int));
// 페이지 테이블 초기화
for (int i = 0; i < num_pages; i++)
    pageTable[i] = -1;
// 물리 프레임 초기화
for (int i = 0; i < NUM_FRAMES; i++)
    physicalMemory[i] = 0;
```

해당 코드를 통해서 페이지 테이블을 모두 초기화하게 된다.

1. **파일 읽기**

```c
// 파일 읽기
const char* filename = "input.txt";
FILE* file = fopen(filename, "r");
if (file == NULL) {
    perror("파일 열기 오류");
    return EXIT_FAILURE;
}
```

fopen 함수를 통해서 현재 디렉터리에 존재하는 input.txt 파일을 읽어들인다.

1. **파일 내 데이터**

```c
// 파일 내 데이터: 가상 메모리 주소
int lineNumber = 0;
while (!feof(file)) {
    char line[MAX_LINE_SIZE];
    fgets(line, MAX_LINE_SIZE, file);

    int address;
    sscanf(line, "%d", &address);

    // 가상 주소에서 페이지 번호(pageNumber)를 얻음
    int pageNumber = getPageNumber(address);

		// pageTable 함수는 페이지 폴트 시 -1 값을 반환함
    int frameNumber = pageTable[pageNumber];
    if (frameNumber == -1) { //page fault
        handlePageFault(pageNumber, policy); //페이지 폴트 핸들러
        frameNumber = pageTable[pageNumber];
    }

    //해당 물리 프레임을 접근하고 접근 횟수를 셈
    physicalMemory[frameNumber]++;

    lineNumber++;
    usleep(1000); //매 페이지 접근 처리 후 0.001초간 멈춤
    //이 delay는 프로세스 수행 중, signal발생 처리과정을 확인하기 위함이며,
    //구현을 수행하는 도중에는 주석처리하여, 빠르게 결과확인을 하기 바랍니다.
}
```

이는 읽어들인 input.txt 파일에 대해서 한 줄씩 fgets 함수를 통해서 읽어들인다. `getPageNumber` 함수는 파라미터로 받은 값을 `page_size(8192)`로 나눈 값을 반환한다. 이를 pageNumber로 대입하고, 이를 통해서 페이지 테이블에서 값을 참조하게 된다.

그 다음 pageTable[pageNumber]의 값을 frameNumber에 대입하는 것을 알 수 있는데, pageTable은 모두바로 위에서 -1으로 초기화되는데, pageTable[pageNumber]을 참조한 값이 -1인 경우에 페이지 폴트 핸들러 함수인 `handlePageFault(pageNumber, policy)` 함수를 실행시키기고 frameNumber에 pageTable[pageNumber] 값을 집어넣는다. 맨 처음에는 -1로 초기화했기 때문에 전체적인 페이지 폴트가 당연하게 발생한다. 하지만 `handlePageFault` 함수는 policy를 파라미터로써 받고 있지만, 바로 알고리즘에 의해 페이지 테이블을 채우는 것이 아니라, 맨 처음 64개의 프레임에는 순차적으로 할당한다.

여기서 핵심 기능이 되는 `handlePageFault` 함수는 밑에 상술하도록 한다.

1. **마무리**

```c
	...
	fclose(file);
	free(pageTable);

	// 작업 수행 완료. Alarm 시그널을 기다림.
	processDone = 1;
	printf("프로세스가 완료되었습니다. 종료 신호를 기다리는 중...\n");
	while (contFlag == 0){};


	// 결과 출력
	printf("\n---물리 프레임 별 접근 횟수----\n");
	for (int i = 0; i < NUM_FRAMES; i++) {
	    printf("[%03d]frame: %d\n", i, physicalMemory[i]);
	}
	printf("----------\n페이지 폴트 횟수: %d\n", pageFaults);
	return 0;
}
```

`fopen()` 함수를 통해 열었던 input.txt파일을 닫고, 프로세스의 종료 신호인 processDone을 1로 설정한다. `main()` 함수의 시작 부분에서 커스텀 시그널 핸들러를 등록했는데, 해당 커스텀 시그널 핸들러에 의하면 키보드 인터럽트를 통해 contFlag = 1로 설정할 수 있고, 그 결과로 프로그램은 결과를 남기고 종료되게 된다.

```c
//TODO-1. 'Ctrl+C' 키보드 인터럽트(SIGINT) 발생 시 처리 루틴
void myHandler(int signum) {
    //SIGINT 시그널 발생 시 기본 동작
    printf("\n(Interrupt) 현재까지 발생한 페이지폴트의 수: %d\n", pageFaults);

    //모든 작업이 완료되었을 시, 시그널 발생 시 동작:
    if (processDone == 1) {
        //1. contFlag 변수를 수정하여 프로세스가 종료될 수 있도록 함.
        contFlag = 1;
        //2. '학번/이름'을 출력함
        printf("2021440008/강형준\n");
    }
}
```

커스텀 핸들러에서 contFlag를 설정하는 로직은 다음과 같다. contFlag가 1로 설정됨으로써 키보드 인터럽트로 꺼지지 않던 프로그램이 종료된다. 다음으로는 `handlePageFault` 함수에 대해서 알아보자.

### `void handlePageFault(int pageNumber, char policy)` - 페이지 폴트 발생

해당 함수는 페이지 폴트가 발생했을 때 실행되는 함수이다. 구체적으로 설명을 덧붙이면, pageTable[pageNumber]의 값이 -1인 경우에 해당 함수가 실행되게 된다. 코드는 다음과 같다.

```c
void handlePageFault(int pageNumber, char policy) {
    int frameNumber = -1; //페이지 폴트 시 사용할 물리 페이지 번호(index)

    // 사용하지 않는 프레임을 순차적으로 할당함
    // (p.s. 실제 시스템은 이런식으로 순차할당하지 않습니다.)
    static int nextFrameNumber = 0;
    static int frameFull = -1;      //모든 물리프레임이 사용된 경우 1, 아닌 경우 -1

    //물리 프레임에 여유가 있는 경우
    if (frameFull == -1) {
        frameNumber = nextFrameNumber++;
        //모든 물리 프레임이 사용된 경우, 이를 마크함
        if(nextFrameNumber == NUM_FRAMES)
            frameFull = 1;
    }
    //모든 물리 프레임이 사용중. 기존 페이지를 교체해야 함
    else {
        //TODO-4. 페이지 교체 알고리즘을 통해 교체될 페이지가 저장된 물리 프레임 번호를 구함
        frameNumber = doPageReplacement(policy);
    }

    // 페이지 테이블 업데이트
    pageTable[pageNumber] = frameNumber;

    printf("페이지 폴트 발생: 페이지 %d를 프레임 %d로 로드\n", pageNumber, frameNumber);
    pageFaults++;
}
```

해당 코드에서 가장 중요한 포인트는 if문이다. 맨 처음에 물리 프레임에 여유가 있는 경우는 순차적으로 사용하지 않는 프레임을 할당하게 된다. 맨 처음 모든 pageTable이 -1로 초기화되고, pageTable[pageNumber]의 값이 -1인 경우, 순차적으로 프레임을 할당하는 것을 고려하면 어떤 페이지 알고리즘을 사용하던 간에 첫 64개의 프레임은 순차적으로 할당하는 것을 알 수 있다.

그 후 모든 물리 프레임에 값이 할당되어 frameFull의 값이 1이 되면 else문 내부에 있는 `doPageReplacement()` 함수를 통해서 페이지를 교체할 페이지가 선택된다. 페이지 교체 알고리즘을 테스트하기 위해 다음과 같은 알고리즘을 구현하였다.

- `d` : 순차 교체 알고리즘 ( 기본적으로 제공됨 )
- `r` : 랜덤 교체 알고리즘 ( 과제 )
- `a` : LRU(Least Recently Used) 알고리즘 ( 추가 구현 )
- `b` : Clock 알고리즘 ( 추가 구현 )

### 순차 교체 알고리즘

순차 교체 알고리즘은 가장 간단한 알고리즘으로 단순하게 가상 메모리의 페이지 주소를 1씩 증가시키며 희생될 페이지를 선택하는 방법이다.

### 랜덤 교체 알고리즘

랜덤 교체 알고리즘은 `rand()` 함수를 통해 랜덤으로 생성한 난수를 통해 페이지 테이블에 있는 희생될 페이지를 선택하는 알고리즘이다.

### LRU 알고리즘

**LRU**는 **Least Recently Used** 알고리즘으로, ‘오랫동안 사용되지 않은 페이지는 필요하지 않을 것이다’ 라는 휴리스틱에 기반하여 가장 마지막에 참조된 페이지를 희생 페이지로 선택하는 알고리즘이다. 해당 알고리즘을 구현하는 방법은 다양하지만, 필자는 이를 내부적으로 구현하기 위해서 matrix의 자료구조를 써서 구현하였다. (Ref 11)

![Untitled](images/Untitled%208.png)

원리는 다음과 같다. 맨 처음 N _ N 비트로 구성된 행렬을 갖는 LRU 하드웨어를 이용한다 ( 해당 프로그램에서는 64 _ 64 이다 ) 행렬 모든 값을 0으로 초기화 한 다음, 페이지 프레임 k가 참조되면 하드웨어는 행렬에서 k번째 행의 모든 비트를 1로 설정, 그리고 k번째 열의 모든 비트를 0으로 설정한다. 그렇게 되면, 이 행렬에서 열의 이진수를 모든 합친 값이 가장 작은 열에 대응되는 페이지 프레임이 가장 과거에 참조된 것이 된다. ( 사진 참고 ) 해당 원리를 C 소스 코드로 구현한 내용은 아래와 같다.

```c
// LRU using a matrix
// LRU 행렬
int lruMatrix[NUM_FRAMES][NUM_FRAMES];

// LRU 초기화 함수
void initializeLRU() {
    int N = NUM_FRAMES;
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            lruMatrix[i][j] = 0;
        }
    }
}

// 특정 페이지 프레임을 참조했을 때 LRU 행렬 업데이트 함수
void updateLRUMatrix(int pageFrame) {
    int N = NUM_FRAMES;
    // 특정 페이지 프레임에 대응되는 행의 모든 비트를 1로 설정
    for (int i = 0; i < N; i++) {
        lruMatrix[pageFrame][i] = 1;
    }

    // 특정 페이지 프레임에 대응되는 열의 모든 비트를 0으로 설정
    for (int i = 0; i < N; i++) {
        lruMatrix[i][pageFrame] = 0;
    }
}

// LRU 알고리즘을 이용하여 다음에 교체될 페이지 프레임 반환 함수
int getNextLRUFrame() {
    int N = NUM_FRAMES;
    int minRowIndex = 0;
    int minRowSum = N + 1;

    // 가장 작은 행을 찾기
    for (int i = 0; i < N; i++) {
        int rowSum = 0;
        for (int j = 0; j < N; j++) {
            rowSum += lruMatrix[i][j];
        }

        if (rowSum < minRowSum) {
            minRowSum = rowSum;
            minRowIndex = i;
        }
    }

    return minRowIndex;
}
```

LRU 구현에 사용된 주된 함수들은 위와 같다. 선택된 프레임에 대응되는 열은 모두 0으로 초기화하여, 이 페이지 프레임을 제외한 나머지는 1이 하나 쌓이게 된다. 그 결과 바뀐 페이지는 열이 모두 0으로 초기화되어, 이진 값의 합이 0이 되지만 다른 참조되지 않은 페이지들은 1이 하나씩 쌓이게 된다. 이렇게 행렬 관점에서 점점 1이 쌓이게 된 열을 ‘오랜 시간동안 참조되지 않았다’ 라고 판단하여 해당 페이지를 희생 페이지로 선택하게 된다.

### Clock 알고리즘

Clock 알고리즘은 모든 페이지를 원형으로 돌아가면서 계속 훑는다. LRU을 약간 개선한 알고리즘인데, Second Chance 알고리즘이라고도 부른다. 기회를 두번 주기 때문에 Second Chance라고 부르며, 원리는 같지만 사용하는 자료형이 다르다. Clock 알고리즘은 원형으로 구현하며 다음과 같은 구조를 띤다. (Ref 11)

![Untitled](images/Untitled%209.png)

위 알고리즘을 구현하기 위해서 **배열(ReferenceBit)**을 생성하고, **시계 초침(clockHand)**를 증가시켜가면서 최근에 참조되었는 지 아닌 지 체크하는 로직을 집어넣었다. Seconde Chance라는 이명에 걸맞게 레퍼런스 비트라는 배열의 값에 따라서 한 번의 기회를 준다.

```c
// Clock 알고리즘 관련
int ReferenceBit[NUM_FRAMES] = {0};
int clockHand = 0;

void setReferenceBit(int frameNumber) {
    ReferenceBit[frameNumber] = 1;
}
```

`ReferenceBit[NUM_FRAMES]`는 물리 프레임에 맞춰 해당 프레임이 최근에 참조되었는 지를 나타내는 배열이고, `clockHand`는 초침을 의미한다. 또한 `setReferenceBit()` 함수는 페이지 폴트 후, 페이지를 교체할 때, 교체한 페이지의 참조 비트를 1로 설정함으로써 다음번 clockHand에 의해 희생 페이지로 설정되는 것을 방지하는 역할을 한다.

이렇게 함수를 설정함과 동시에 handlePageFault() 함수에서 전역적으로 사용하는 내용에 캐시 데이터에 대한 업데이트가 필요하다.

```c
// 페이지 폴트 처리
void handlePageFault(int pageNumber, char policy) {
		...

    // LRU 매트릭스 업데이트
    updateLRUMatrix(pageTable[pageNumber]);

    // Clock 레퍼런스 비트 업데이트
    setReferenceBit(pageTable[pageNumber]);

	  ...
}
```

LRU, Clock 알고리즘을 구현한 다음, 위 함수에 다음 코드를 삽입하여, 알고리즘이 state를 기억하기 위해 만들어둔 전역 변수에 대한 값을 갱신하는 과정을 통해서 LRU 및 Clock 알고리즘을 구현했다.

> Page offset 크기를 다르게 입력하여 결과물을 비교

**순차 교체 알고리즘**의 페이지 오프셋 크기를 다르게 하여 페이지 폴트의 발생 횟수를 비교한 결과는 다음과 같다.

| 페이지 오프셋   | 10  | 11  | 12  | 13  | 14  | 15  | 16  |
| --------------- | --- | --- | --- | --- | --- | --- | --- |
| 페이지 폴트(번) | 772 | 689 | 589 | 565 | 526 | 472 | 378 |

![Untitled](images/Untitled%2010.png)

그래프를 통해서 나타내면 다음과 같다. 선명하게 우하향 그래프를 얻을 수 있었다. 페이지 오프셋과 페이지 폴트의 횟수는 반비례하는 것을 알 수 있었는데, 어떠한 이유로 이러한 상관관계를 가지는 것일까?

페이지 오프셋은 컴파일된 프로그램을 실행 시킬 때, 첫 번째 인자로 넣어주게 된다. 넣어주게 된 인자는 `atoi()` 함수를 통해서 정수로 타입이 변환되어 `page_bits` 변수에 대입되고, `calculatePageInfo(page_bits)` 가 실행되게 된다. 해당 함수의 내용은 다음과 같다.

```c
#define ADDR_SIZE 27 //주어진 시스템은 27-bit 주소를 사용함

// 중략

void calculatePageInfo(int page_bits) {
    page_size = 1 << page_bits;
    num_pages = 1 << (ADDR_SIZE - page_bits);
}
```

위 코드를 통해서 page_size와 num_pages가 결정되게 된다. 여기서 사용하는 **<<** 기호는 비트 시프트 연산자이며, 주어진 비트 수 만큼 왼쪽으로 이동시키는 것이다. page_bits가 8이라고 가정하면 page_size는 100000000이 되기 때문에 $2^8$이 되게 된다.

page_size는 페이지의 크기를 나타내는 변수이다. 비트 시프트 연산자를 쓰기 때문에 **2의 page_bits 제곱**을 의미한다. num_page는 전체 주소 공간을 페이지 크기로 나눈 결과로 **페이지의 수**를 나타내게 된다.

예를 들어 `calculatePageInfo(12)`를 호출하게 된다면 page_size는 2의 12승이 되어 4096이 된다. 이는 일반적인 페이지 크기인 4KB를 나타낸다. num_pages는 27-12로 계산되어 전체 주소 공간을 4KB로 나눈 페이지 수를 나타내게 된다.

그렇다면 페이지 비트가 커짐에 따라서 페이지 폴트가 줄어드는 반비례 관계를 보이는 이유는 뭘까? 페이지의 크기가 커짐에 따라 페이지에 더 많은 데이터가 저장될 수 있어서 메모리의 일부를 더 효율적으로 활용할 수 있게 되기 때문이다. 실제로 다음 명령어를 통해서 페이지의 크기가 큰 경우의 결과값을 다음과 같다.

- 입력 : `gcc test.c && ./a.out 20 d`
- 출력 :

```bash
입력된 페이지 별 크기: 1048576Bytes
프로세스의 페이지 개수: 128개
페이지 교체 알고리즘: d

..

---물리 프레임 별 접근 횟수----
[000]frame: 820
[001]frame: 52
[002]frame: 568
[003]frame: 304
[004]frame: 112
[005]frame: 86
[006]frame: 1477
[007]frame: 828
[008]frame: 88
[009]frame: 64
[010]frame: 116
[011]frame: 1116
[012]frame: 725
[013]frame: 368
[014]frame: 132
[015]frame: 112
[016]frame: 88
[017]frame: 960
[018]frame: 556
[019]frame: 312
[020]frame: 52
[021]frame: 88
[022]frame: 24
[023]frame: 60
[024]frame: 40
[025]frame: 32
[026]frame: 32
[027]frame: 36
[028]frame: 40
[029]frame: 32
[030]frame: 96
[031]frame: 16
[032]frame: 12
[033]frame: 4
[034]frame: 48
[035]frame: 24
[036]frame: 8
[037]frame: 224
[038]frame: 72
[039]frame: 8
[040]frame: 24
[041]frame: 32
[042]frame: 4
[043]frame: 96
[044]frame: 4
[045]frame: 8
[046]frame: 0
..
[063]frame: 0
----------
페이지 폴트 횟수: 46
```

- 입력 : `gcc test.c && ./a.out 23 d`
- 출력 :

```bash
입력된 페이지 별 크기: 8388608Bytes
프로세스의 페이지 개수: 16개
페이지 교체 알고리즘: d

..

---물리 프레임 별 접근 횟수----
[000]frame: 6318
[001]frame: 276
[002]frame: 1460
[003]frame: 120
[004]frame: 470
[005]frame: 212
[006]frame: 204
[007]frame: 576
[008]frame: 200
[009]frame: 68
[010]frame: 88
[011]frame: 8
[012]frame: 0
..
[063]frame: 0
----------
페이지 폴트 횟수: 12
```

인자로 전달하는 값이 3 커짐에 따라서 **입력된 페이지 별 크기**는 \*\*\*\*1048576Bytes에서 8388608Bytes로 약 $2^3$배가 되었고, 프로세스의 페이지 개수는 반대로 $2^3$배가 줄었다. 당연하게 페이지 폴트 횟수도 줄었다. 이렇게 프레임의 크기가 커지기 때문에 페이지 폴트로 인하여 다른 프레임에 값을 넣을 필요가 없어지기 때문에 페이즈 폴트의 횟수가 줄어들게 되는 것이다.

결론적으로 위와 같은 이유로 페이지 비트에 따라 페이즈 폴트 횟수는 반비례하게 된다. 하지만 너무 큰 페이지 크기를 선택하는 것은 항상 좋은 결과를 초래하는 것은 아니다, 작은 페이지 크기는 작은 공간 지역성을 활용하는데 유리할 수 있으며, 메모리 내의 작은 변경 사항이 전체 페이지를 다시 로드해야하는 큰 오버헤드를 초래할 수도 있기 때문에. 페이지 크기를 정할 때에는 적절한 크기를 정하는 것이 좋다.

> Page replacement algorithm을 다르게 하여 결과물을 비교

알고리즘은 총 네가지를 사용했다. 순차 교체 알고리즘, 랜덤 교체 알고리즘, LRU 알고리즘, Clock 알고리즘을 통해서 페이지 교체 알고리즘을 테스트해보았는데, 표로 나타내면 다음과 같다. Page offset을 8부터 20까지 4씩 올려가서 테스트하였으며, 입력에 따라 항상 같은 결과를 나타내는 멱등성이 없는 랜덤 교체 알고리즘은 다섯 번의 실행값의 평균을 기록하였다.

| 페이지 오프셋에 따른 페이지 폴트 횟수/알고리즘 | 순차 교체 | 랜덤 교체 | LRU  | Clock |
| ---------------------------------------------- | --------- | --------- | ---- | ----- |
| 4                                              | 4908      | 4910      | 4908 | 4908  |
| 8                                              | 1015      | 1027      | 1007 | 1007  |
| 12                                             | 589       | 610       | 578  | 578   |
| 16                                             | 378       | 386       | 369  | 369   |
| 20                                             | 46        | 46        | 46   | 46    |

알고리즘에 따라 생각보다 큰 값의 차이가 나질 않았는데, 이는 특히 페이지 오프셋이 클 수록 차이가 거의 나지 않았다. 앞서 설명한 것처럼 페이지 테이블을 초기에 모두 -1로 초기화하고, 이러한 이유로 초반에는 필연적으로 순차적으로 물리 프레임을 앞에서부터 채운다. 페이지 오프셋이 20을 주는 경우에는 아예 초반에 순차 할당하는 과정에서 끝나버리기 때문에 모든 교체 알고리즘에서 페이지 폴트 횟수가 46으로 끝나버렸다.

또한 **LRU(Least Recently Used)** 알고리즘 같은 경우에는 모든 리스트를 순회하여 가장 쓰이지 않았던 페이지를 내려야하기 때문에 페이지 오프셋을 4로 설정한 경우에는 순차 교체나 랜덤 교체에 비해서 높은 메모리 사용률과 시간이 오래 걸렸다. 이는 다른 알고리즘이 O(N)의 시간복잡도를 가지는 데에 비해 LRU는 매트릭스 자료구조를 통해 이중 포문으로 구현하여 O($N^2$)의 시간복잡도를 가지고 있기 때문에 오래 걸리는 것이라고 볼 수 있다.

**Clock** 알고리즘의 결과는 **LRU**와 같은데, 이는 같은 LRU와 비슷한 알고리즘에 참조에 따라 기회를 한 번 더 주는 것인데, input.txt에서의 input 값이 재참조를 발생시키지 않기 때문에 LRU와 같은 결과가 나온다는 것을 알 수 있었다. 단, 매트릭스 자료구조를 위해 이중 포문으로 구현한 LRU와는 다르게 원형큐 자료형을 사용하였기 때문에 낮은 시간복잡도로 메모리 사용량이 LRU보다 낮다는 것을 프로파일링할 수 있었다.

> 과제를 수행하면서 어려웠던 점, 이를 어떻게 해결하였는지(또는 해결하지 못한
> 이유)를 작성하여 보고서의 마지막에 기술.

과제를 수행하면서 역시 가장 어려웠던 점은 페이징 알고리즘을 직접 스켈레톤 코드에 구현하는 것이었다. 평소에 C를 통한 자료구조나 알고리즘에는 익숙했지만, 기존의 코드를 이해하지 못한 채로 먼저 구현하려고 했더니 생각보다 어려웠다. 이를 해결하기 위해서 순서를 조금 틀어, **Part#1의 자료 조사 → 기존의 코드 설명 → 기능 구현 → 구현한 내용 설명** 이러한 순서를 거쳐 페이징에 대한 기본적인 개념 이해와 기존 코드를 이해하고 난 후 구현하려고 하니 맨 처음보다 훨씬 쉽고 빠르게 구현할 수 있었다.

또 다른 힘들었던 점은 하드웨어에 가까운 Low level 일수록 참고할만한 레퍼런스의 수가 현저히 적었다. 벨로그 및 티스토리와 같은 개발자 블로그에서는 어플리케이션 레벨이나 사용자 모드 레벨에 대해서 다루는 내용은 많지만, 커널 레벨이나 하드웨어(임베디드) 레벨까지 다루는 자료는 거의 찾지 못했고 공신력이 있는 자료인 지 확인하기 어려웠다. 충분한 정보를 찾기 위해서 대부분의 레퍼런스를 공식 문서에서 따왔는데, 전문이 영어로 쓰여있기 때문에 조사하는 데 생각보다 오래 걸렸던 것 같다.

마지막으로는 하드웨어 레벨에서의 페이징을 이해하는 방식이 어려웠다. 알고리즘의 구현을 통해서 결과값을 얻어내 표를 만들어냈지만, 단순한 페이지 폴트 결과만으로는 하드웨어 레벨에서 정상적으로 작동하는 지에 대한 검증이 힘들었다. 특히 LRU와 Clock 알고리즘에서의 페이지 폴트 횟수가 차이가 없는 것에 대해서 이를 프로파일링하기 위해 파이썬 스크립트를 통해서 input.txt 파일을 프로파일링했다.

```python
def check_duplicate_elements(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()

            # 공백 및 개행문자 제거 및 중복 확인
            clean_lines = [line.strip() for line in lines]
            duplicates = set(x for x in clean_lines if clean_lines.count(x) > 1)

            if duplicates:
                print("중복된 요소가 있습니다:")
                for duplicate in duplicates:
                    print(f"- {duplicate}")
            else:
                print("중복된 요소가 없습니다.")
    except FileNotFoundError:
        print(f"파일 '{file_path}'을 찾을 수 없습니다.")

# input.txt 파일의 경로를 지정하여 함수 호출
check_duplicate_elements("input.txt")
```

결과는 다음과 같다.

```bash
 ~/sources/system_programming) $ python3 check_input.py
중복된 요소가 있습니다:
- 29486864
- 64
- 29486896
- 29486872
- 29486904
- 33883296
- 24392392
- 21238344
- 29486944
- 29486968
- 132807468
- 29486856
- 29486960
- 33
- 33883320
- 24392384
- 33883264
- 33883272
- 29486880
- 21238352
- 33883312
- 67
- 29486952
- 24392400
- 21238360
- 33883288
- 21238336
- 33883280
- 24392408
- 29486888
- 33883304
- 29486848
```

이렇게 파이썬 스크립트를 통해 검증한 결과 LRU 알고리즘은 64번의 페이지 폴트 동안의 기회를 주는 반면 Clock은 128번의 페이지 폴트 동안 쓰이지 않는 프레임에 대해 페이지 교체를 실행한다. 중복된 값의 라인을 확인하는 프로파일링 스크립트에 대한 결과는 다음과 같다.

```bash
- '132807468' : 등장 라인 [73, 9781, 9783, .. 9981, 9982, 9986, 9987]
- '67' : 등장 라인 [74, 9787, 9794, .. 9976, 9983]
- '64' : 등장 라인 [75, 9782, 9788, .. 9984, 9985]
- '24392384' : 등장 라인 [1684, 9934]
- '24392392' : 등장 라인 [1685, 9935]
- '24392400' : 등장 라인 [1686, 9932]
- '24392408' : 등장 라인 [1687, 9933]
- '33883280' : 등장 라인 [2220, 9954]
- '33883288' : 등장 라인 [2221, 9955]
- '33883264' : 등장 라인 [2222, 9952]
- '33883272' : 등장 라인 [2223, 9953]
- '33883296' : 등장 라인 [2224, 9956]
- '33883304' : 등장 라인 [2225, 9957]
- '33883312' : 등장 라인 [2226, 9958]
- '33883320' : 등장 라인 [2227, 9959]
- '29486944' : 등장 라인 [3488, 9988]
- '29486952' : 등장 라인 [3489, 9989]
- '29486960' : 등장 라인 [3490, 9990]
- '29486968' : 등장 라인 [3491, 9991]
- '29486856' : 등장 라인 [4068, 9993]
- '29486848' : 등장 라인 [4069, 9992]
- '29486872' : 등장 라인 [4070, 9995]
- '29486864' : 등장 라인 [4071, 9994]
- '29486880' : 등장 라인 [4072, 9996]
- '29486888' : 등장 라인 [4073, 9997]
- '29486896' : 등장 라인 [4074, 9998]
- '29486904' : 등장 라인 [4075, 9999]
- '21238336' : 등장 라인 [4548, 9949]
- '21238344' : 등장 라인 [4549, 9948]
- '21238352' : 등장 라인 [4550, 9951]
- '21238360' : 등장 라인 [4551, 9950]
- '33' : 등장 라인 [6354, 9945]
```

LRU 알고리즘은 64번의 프레임을 돌아서 사용되지 않는 페이지를 희생 페이지로 정하는 것이었고, Clock 알고리즘은 기회를 한 번 더 주어 128번 프레임을 돈다 ( 64번씩 두 바퀴 ) 위 데이터 셋의 결과 Clock과 LRU의 페이지 폴트 차이를 결정할 64번과 128번 사이 간격을 가진 페이지 데이터 라인이 나오지 않는 것을 확인할 수 있었다. 따라서 LRU과 Clock 알고리즘의 결과는 같게 나온다. 이와 같은 하드웨어 수준에서의 결과를 프로파일링하는 것이 힘들었다.

> 추가 고찰

### C의 signal.h에 대하여

IBM에서 <signal.h> 헤더 파일에 대한 정보를 찾아보면 `signal()` 과 `raise()` 함수를 선언하며, 다음 매크로를 정의한다고 한다.

| SIGABRT
SIGALL
SIG_DFL | SIG_ERR
SIGFPE
SIG_IGN | SIGILL
SIGINT
SIGIO | SIGOTHER
SIGSEGV
SIGTERM | SIGUSR1
SIGUSR2 |
| --- | --- | --- | --- | --- |

(Ref 6)을 통해서 다양한 시그널들을 확인할 수 있었는데, signal.h 헤더 파일에서는 다음과 같이 매크로를 정의할 수 있다는 것을 알 수 있었다. 위 소스 코드에서는 `SIGINT`에 대해서 커스텀 시그널 핸들러를 등록하는데, 이는 표에 따르면 키보드에 의한 인터럽트라고 한다.

실제로 프로그램 작동 시 `^C` 를 통해 인터럽트를 동작시킬 수 있었고, 커스텀 시그널 핸들러의 동작을 확인했다. signal.h이 감싸고 있는 POSIX API를 확인하기 위해서 gcc 명령어로 컴파일 하는 점을 참고하여 커널 수준에서 작동되는 함수들을 살펴보았다. (Ref 8)

`sig` 로 시작하는 prefix를 가진 POSIX API를 사용하는 것으로 확인할 수 있었고, 다음과 같은 것들이 POSIX API가 있는 것을 확인할 수 있었다. (Ref 9)

| sigaction | sigpending  | sigprocmask  |
| --------- | ----------- | ------------ |
| sigqueue  | sigsuspend  | sigtimedwait |
| sigwait   | sigwaitinfo |              |

몇몇 개의 POSIX API 명을 제외하고는 직관으로 사용 목적을 확인할 수 있었다. GCC는 다음과 같은 POSIX를 통해 signal을 처리하는 프로그램을 컴파일한다.

### Linux의 Page Replacement Policy

위에서 리눅스는 LRU(Least Recently Used) 알고리즘 기반이라고 써 두었는데, 이는 대부분의 문서에서 LRU 기반이라는 설명만으로 뭉뚱그려 넘어가지만 공식 문서를 두면 LRU 알고리즘을 개선한 Clock 알고리즘에 기반을 둔다고 한다. (Ref 5)

<aside>
<img src="https://www.notion.so/icons/document_gray.svg" alt="https://www.notion.so/icons/document_gray.svg" width="40px" /> The lists described for 2Q presumes Am is an LRU list but the list in Linux closer resembles a Clock algorithm [[Car84](https://www.kernel.org/doc/gorman/html/understand/understand031.html#carr84)] where the hand-spread is the size of the active list. When pages reach the bottom of the list, the referenced flag is checked, if it is set, it is moved back to the top of the list and the next page checked. If it is cleared, it is moved to the inactive_list.

</aside>

다음 설명에 따르면 LRU이라고 일반적으로 생각하지만 리눅스는 Hand-spread가 활성 목록의 크기인 Clock 알고리즘과 닮아있다고 한다. 해당 레퍼런스(Ref 5)에서는 Clock-Pro라는 표헌을 쓰고 있지 않지만, 다른 자료에 따르면 리눅스의 페이지 교체 알고리즘을 Clock-Pro라고 부르는 것을 확인할 수 있었다. (Ref 10)

LRU에 기반을 두는 이유는 다음과 같은 간단한 추론 때문에다. ‘페이지가 오랫동안 사용되지 않았다면 가까운 시일 내에 다시 필요하지 않을 것이다.’ 이러한 추론에서 시작하여 LRU를 도입한다. 하지만 순수한 LRU 알고리즘을 통해서 모든 페이지를 스캔하는 것은 감당할 수 없는 오버헤드를 가지고 있기 때문에 위 설명에 따라 active_list 와 inactive_list를 도입한 **개선된 LRU 방식**을 사용하게 되었다.

하지만 이러한 개선된 LRU 메커니즘은 특정 케이스에서 무너지는 경향이 있었는데, 대규모 배열 초기화나 대용량 파일 읽기(ex: 스트리밍 미디어 재생), 파일 시스템의 상당 부분을 탐색하는 등의 작업은 곧 다시 사용되지 않을 페이지로 주 메모리를 꽉 채울 수 있는 문제점이 있다.

이러한 문제점을 개선하기 위해서 Song jiang, Feng Chen 및 Xiaodong Zhang이 개발한 **Clock-Pro 알고리즘**을 사용한다고 한다. 이 알고리즘은 페이지에 엑세스 하는 빈도를 추적하고 일치하도록 VM 코드의 동작을 조정하여 LRU 접근 방식을 넘어서려고 시도한다. 기본적으로 Clock-Pro 알고리즘은 비활성 목록(inactive_list)의 페이지가 활성 목록(active_list)의 페이지보다 덜 자주 참고되도록 시도한다. 따라서 **이는 특정 페이지가 어플리케이션에서 거의 사용되지 않는 경우에도 가장 최근에 엑세스한 페이지에 우선 순위를 두는 LRU 체계**와 다르기 때문에 LRU보다 좋은 퍼포먼스를 보인다.

![(Ref 10)](images/Untitled%2011.png)

(Ref 10)

예를 들어, LRU 알고리즘이었다면 빨간색 선이 지나가는 타이밍(t1 시점)에서 가까운 미래에 다시 사용될 가능성이 높은 페이지 1보다 2를 선호하게 된다.

이러한 이유를 통해서 Linux 계열 운영체제는 페이지 교체 알고리즘을 LRU 방식이 아닌 Clock에 가까운 방식을 사용한다고 한다. Clock 방식을 개량한 Clock-Pro 방식이 리눅스가 사용하고 있는 방식이라고 한다. Clock의 본질적인 원리가 LRU를 사용하고 있는 것을 생각하면 리눅스가 LRU 기반 알고리즘이라는 설명도 완전히 틀린 설명은 아닌 것 같다.

## 참조

7. **[IBM]** docs : [https://www.ibm.com/docs/ko/i/7.3?topic=functions-signal-handle-interrupt-signals](https://www.ibm.com/docs/ko/i/7.3?topic=functions-signal-handle-interrupt-signals)
8. **[GNU]** docs : [https://www.gnu.org/software/libc/manual/html_node/Signal-Handling.html](https://www.gnu.org/software/libc/manual/html_node/Signal-Handling.html)
9. **[Oracle]** docs : [https://docs.oracle.com/cd/E19048-01/chorus5/806-6897/auto1/index.html](https://docs.oracle.com/cd/E19048-01/chorus5/806-6897/auto1/index.html)
10. **[LWN.net]** A CLOCK-Pro page replacement implementation : [https://lwn.net/Articles/147879/](https://lwn.net/Articles/147879/)
11. **[Dragony Velog]** 페이지 교체 알고리즘 : [https://velog.io/@holicme7/OS-메모리관리7-페이지-교체-알고리즘1](https://velog.io/@holicme7/OS-%EB%A9%94%EB%AA%A8%EB%A6%AC%EA%B4%80%EB%A6%AC7-%ED%8E%98%EC%9D%B4%EC%A7%80-%EA%B5%90%EC%B2%B4-%EC%95%8C%EA%B3%A0%EB%A6%AC%EC%A6%981)
