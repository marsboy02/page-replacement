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
