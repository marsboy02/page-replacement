def find_duplicates_with_given_numbers(file_path, numbers):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()

            # 주어진 숫자들을 집합으로 변환
            given_numbers_set = set(numbers)

            # 중복된 숫자를 저장할 딕셔너리
            duplicates = {}

            # 각 숫자의 등장 위치 기록
            number_positions = {}
            for index, line in enumerate(lines):
                number = line.strip()
                if number in number_positions:
                    number_positions[number].append(index + 1)
                else:
                    number_positions[number] = [index + 1]

            # 중복 확인
            for number, positions in number_positions.items():
                if number in given_numbers_set:
                    duplicates[number] = positions

            return duplicates

    except FileNotFoundError:
        print(f"파일 '{file_path}'을 찾을 수 없습니다.")
        return None

# 주어진 숫자들
given_numbers = [
    "29486864", "64", "29486896", "29486872", "29486904",
    "33883296", "24392392", "21238344", "29486944", "29486968",
    "132807468", "29486856", "29486960", "33", "33883320",
    "24392384", "33883264", "33883272", "29486880", "21238352",
    "33883312", "67", "29486952", "24392400", "21238360",
    "33883288", "21238336", "33883280", "24392408", "29486888",
    "33883304", "29486848"
]

# input.txt 파일의 경로와 주어진 숫자들을 지정하여 함수 호출
result = find_duplicates_with_given_numbers("input.txt", given_numbers)

# 결과 출력
if result:
    print("파일에서 발견된 중복된 숫자:")
    for number, positions in result.items():
        print(f"- '{number}' : 등장 라인 {positions}")
