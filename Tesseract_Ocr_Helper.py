import os
import tkinter as tk
import tkinter.font as tkFont
import pyperclip
import threading
import gspread
from tkinter import ttk
from colorama import init, Fore, Style
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime


def wrap_text(text):
    # 입력된 텍스트를 27자씩 나누어 줄바꿈
    wrapped_text = ""
    for i in range(0, len(text), 27):
        wrapped_text += text[i:i+27] + "\n"
    return wrapped_text.strip()

def on_wrap_button_click():
    
    # 버튼 클릭 시 텍스트를 가져와서 텍스트 박스에 나타내기
    input_text = text_entry.get("1.0", "end-1c")  # 1.0부터 end-1c까지의 텍스트 가져오기
    
    # 텍스트가 비어 있는지 확인
    if not input_text:
        status_label.config(text="원본 텍스트가 필요합니다!", fg="red")
        return
    
    # 디렉토리 내의 전 작업물 삭제
    delete_files_in_directory(directory_path)
    
    

    # 줄바꿈 제거
    input_text = input_text.replace('\n', '')
    
    # 줄바꿈된 부분이 전체가 공백이거나 마지막에 '.'만 있는 경우 제거
    result_lines = [line for line in wrap_text(input_text).split('\n') if line.strip() and not line.strip() == '.']
    
    result_text.config(state=tk.NORMAL)  # 텍스트 박스 수정 가능 상태로 전환
    result_text.delete("1.0", tk.END)  # 결과 텍스트 박스 초기화
    result_text.insert(tk.END, "\n".join(result_lines))  # 결과 텍스트 추가
    result_text.config(state=tk.DISABLED)  # 텍스트 박스 읽기 전용 상태로 전환
    
    pyperclip.copy(result_text.get("1.0", "end-1c"))
    
    status_label.config(text="result_text 복사 완료. Trainer에 붙혀넣기 해주세요.")  # 메시지 업데이트

def on_change_box_text_button_click():
    
    
    # 두 번째 버튼 클릭 시 고정된 경로에 있는 모든 "box" 파일의 텍스트를 변경
    box_files = [f for f in os.listdir(directory_path) if f.endswith('.box')]
    
     # 텍스트가 비어 있는지 확인
    if not result_text.get("1.0", tk.END).strip():
        status_label.config(text="원본 텍스트가 필요합니다!", fg="red")
        return

    result_lines = result_text.get("1.0", tk.END).split('\n')

    # 각 파일에 대해 텍스트 변경 작업 수행
    for box_file in box_files:
        # 각 box 파일의 경로 설정
        box_file_path = os.path.join(directory_path, box_file)

        # box 파일 열기
        with open(box_file_path, 'r', encoding='utf-8') as file:
            # 파일의 모든 줄을 읽어옴
            lines = file.readlines()

        # 각 줄의 '#' 뒤와 한 줄 내의 모든 텍스트를 result_text의 해당 줄의 텍스트로 교체하고 줄바꿈 추가
        for i in range(0, len(lines), 2):  # 0부터 시작해서 2씩 증가하는 짝수 번째 줄만 처리
            if '#' in lines[i]:
                # result_text의 내용이 더 적을 수 있으므로 인덱스가 범위를 벗어나지 않도록 조정
                if i // 2 < len(result_lines):
                    lines[i] = lines[i].split('#')[0] + f"#{result_lines[i // 2]}\n"
                

        # 변경된 내용으로 box 파일 덮어쓰기
        with open(box_file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)

    # 처리 완료 문구 추가
    result_text.config(state=tk.NORMAL)  # 텍스트 박스 수정 가능 상태로 전환
    result_text.insert(tk.END, "\n")  # 줄바꿈 추가
    result_text.insert(tk.END, "\n***box파일 수정이 완료되었습니다.***", "blue")  # 결과 텍스트 추가
    result_text.tag_configure("blue", foreground="blue")  # 스타일 적용
    result_text.config(state=tk.DISABLED)  # 텍스트 박스 읽기 전용 상태로 전환
    
    status_label.config(text="변환 완료",fg="green")  # 메시지 업데이트

def on_clean_button_click():
    # Clean 버튼 클릭 시 텍스트 입력 창과 결과 텍스트 박스의 내용을 모두 삭제
    text_entry.delete("1.0", tk.END)
    result_text.config(state=tk.NORMAL)
    result_text.delete("1.0", tk.END)
    result_text.config(state=tk.DISABLED)
    
    status_label.config(text="지우기 완료",fg="green")  # 메시지 업데이트

def delete_files_in_directory(directory):
    for file_name in os.listdir(directory):
        file_path = os.path.join(directory, file_name)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")


def run_tesseract(image_path, output_path, language):
    command = f'tesseract "{image_path}" "{output_path}" -l {language} --psm 6'
    os.system(command)

def process_images(input_directory, output_directory, language):
    
    status_label.config(text="********메모장이 뜰때까지 기다려주세요!********",fg="green")  # 메시지 업데이트
    
    # 출력 디렉토리가 존재하지 않으면 생성
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    print(Fore.BLUE + f"이미지 파일을 {Fore.RED}{language}{Fore.BLUE} 언어로 텍스트로 변환 중입니다_Tesseract" + Style.RESET_ALL)

    # 입력 디렉토리에서 .jpg 확장자를 가진 모든 파일 가져오기
    image_files = [f for f in os.listdir(input_directory) if f.endswith('.jpg')]

    # 파일 이름을 'test'로 시작하고 숫자로 끝나는 순서로 정렬
    image_files.sort(key=lambda x: (x.startswith('test'), int(''.join(filter(str.isdigit, x))) if any(char.isdigit() for char in x) else float('inf')))

    # 각 이미지에 대해 Tesseract 실행
    for image_file in image_files:
        # 이미지 파일 및 결과 출력 파일 경로 설정
        image_path = os.path.join(input_directory, image_file)
        output_path = os.path.join(output_directory, os.path.splitext(image_file)[0])

        # Tesseract 실행 함수 호출
        run_tesseract(image_path, output_path, language)

    # 결과를 합친 텍스트 파일 생성
    combine_and_delete(output_directory, "combined_output.txt")
    
    

def combine_and_delete(output_directory, combined_output_file):
    # 합쳐진 텍스트 파일의 경로 설정
    combined_output_path = os.path.join(output_directory, combined_output_file)

    try:
        # 이미 존재하는 파일 삭제
        if os.path.exists(combined_output_path):
            os.remove(combined_output_path)
    except Exception as e:
        print(f"Error deleting file: {e}")

    # 출력 디렉토리에서 .txt 확장자를 가진 모든 파일 가져오기
    text_files = [f for f in os.listdir(output_directory) if f.endswith('.txt')]

    # 파일 이름을 숫자로 끝나는 순서로 정렬
    text_files.sort(key=lambda x: int(''.join(filter(str.isdigit, x))) if any(char.isdigit() for char in x) else float('inf'))

    # 하나의 텍스트 파일로 결과를 합치기
    with open(combined_output_path, 'w', encoding='utf-8') as combined_output:
        for text_file in text_files:
            text_file_path = os.path.join(output_directory, text_file)
            with open(text_file_path, 'r', encoding='utf-8') as f:
                combined_output.write(f.read())

    # 원본 텍스트 파일 삭제
    for text_file in text_files:
        text_file_path = os.path.join(output_directory, text_file)
        os.remove(text_file_path)

    # 합쳐진 텍스트 파일 열기
    os.system(f'start notepad "{combined_output_path}"')
    #구글시트
    update_google_sheets()

def on_Test_button_click():
    selected_language = language_combobox.get()
    process_images_threaded(selected_language)
    
    
def process_images_threaded(selected_language):
    status_label.config(text="이미지 변환 및 합침 진행 중...")
    thread = threading.Thread(target=process_images, args=(input_directory, output_directory, selected_language))
    thread.start()
   
   
def update_google_sheets():
    # Google Sheets API 인증 설정
    scope = 'https://spreadsheets.google.com/feeds'
    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_key_path, scope)
    gc = gspread.authorize(credentials)

   
    doc = gc.open_by_url(sheet_url)
    worksheet = doc.worksheet('output_save')

    
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # timestamp 생성
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 데이터를 Google Sheets에 추가
    data_to_insert = [timestamp,""] + [line.strip() for line in lines]
    worksheet.append_row(data_to_insert)

    status_label.config(text="데이터가 성공적으로 Googlesheet에 추가되었습니다.",fg="green")
    
#def background_process(selected_language):
#    # 여기에 백그라운드에서 수행될 작업을 추가
#    process_images(input_directory, output_directory, selected_language)
    
   
    


    
    
# Tkinter 윈도우 생성
app = tk.Tk()

default_font = tkFont.nametofont("TkDefaultFont")
default_font.configure(family='맑은 고딕', weight='bold')
app.title("Tesseract_Ocr_Helper Ver.1")

# Box데이터를 수정하고 삭제할 경로 
directory_path = "C:\\Users\\karuj\\Desktop\\Tesseract Workspace"
# 입력 이미지가 있는 디렉토리 경로 
input_directory = "C:\\Users\\karuj\\Desktop\\test Image"
# Tesseract 결과를 저장할 디렉토리 경로 
output_directory = "C:\\Users\\karuj\\Desktop\\Tesseract Workspace\\ocroutput"
# Google Sheets url
sheet_url = 'https://docs.google.com/spreadsheets/d/1ZvBm_nbNHFZdhOdemLJMgm6I5CyxAYgQ6yids66lYuU/edit#gid=2030746116'
# jsonKey 경로
json_key_path = os.path.abspath('C:\\Users\\karuj\\Desktop\\Tesseract_Ocr_Helper\\tesseract-train-1c726ddac2a6.json')
# Google Sheet에 올린 텍스트파일 경로
file_path = 'C:\\Users\\karuj\\Desktop\\Tesseract Workspace\\ocroutput\\combined_output.txt'

    
    

# 응용프로그램 크기 설정
app.geometry("480x600")

# 텍스트 입력 창
text_entry = tk.Text(app, height=13, width=65, wrap=tk.WORD)
text_entry.grid(row=0, column=0, columnspan=2, pady=10, padx=10)

# 결과 텍스트 박스 (읽기 전용)
result_text = tk.Text(app, height=14, width=65, wrap=tk.WORD, state=tk.DISABLED)
result_text.grid(row=1, column=0, columnspan=2, pady=10, padx=10)

# 주의사항 설명 레이블
wrap_button_label = tk.Label(app, text="⚠️⚠️Wrap Text 버튼을 누를시⚠️⚠️ \nWorkspace 경로의 모든 box,tif,lstmf 파일이 삭제됩니다.\n반드시 한 학습이 끝나고 실행해주세요.", font=('맑은 고딕', 8), fg="red")
wrap_button_label.grid(row=2, column=0, columnspan=2, pady=2)

# Wrap 버튼 
wrap_button = tk.Button(app, text="Wrap Text", command=on_wrap_button_click)
wrap_button.grid(row=3, column=0, pady=2, padx=(20, 60))

# Change Box Text 버튼
change_box_text_button = tk.Button(app, text="Change Box Text", command=on_change_box_text_button_click)
change_box_text_button.grid(row=3, column=0, columnspan=2, pady=10)

# Clean 버튼
clean_button = tk.Button(app, text="Clean", command=on_clean_button_click)
clean_button.grid(row=3, column=1, pady=10, padx=(40, 0)) 

# 상태 레이블
status_label = tk.Label(app, text="", fg="green")
status_label.grid(row=4, column=0, columnspan=2, pady=5)

# 콤보박스 위젯
language_combobox = ttk.Combobox(app, values=["kor+eng","eng+kor", "kor", "eng"], width=15, height=30, state="readonly")
language_combobox.set("kor+eng")  # 초기 선택값 설정
language_combobox.grid(row=5, column=0, pady=10, padx=(10, 5), sticky=tk.E)  # Updated row, padx, and sticky values

# 이미지 테스트 버튼
image_test_button = tk.Button(app, text="ImageTest", command=on_Test_button_click)
image_test_button.grid(row=5, column=1, pady=10, padx=(5, 10), sticky=tk.W)  # Updated row, padx, and sticky values

# Tkinter 이벤트 루프 시작
app.mainloop()
