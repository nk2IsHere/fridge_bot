# coding: utf-8
# Распознавание овощей, подсчет
import cv2 as cv


# Функция вывода изображения:
def show(img, name):
    cv.imshow(name, img)
    while True:
        if cv.waitKey(1) == 27:
            break  # esc to quit
    cv.destroyAllWindows()

	
# Инициализация камеры:
def cam_init():
    cap = cv.VideoCapture(0)
    frame_width = 640
    frame_height = 480

    cap.set(3, frame_width)
    cap.set(4, frame_height)
    frame_center = frame_height / 2


def get_tomato():
    ### Предобработка
    # Чтение изображения:
    ret, img = cap.read()
    img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
    #show(img, 'original')

    # To gray:
    gray = cv.cvtColor(img, cv.COLOR_RGB2GRAY)
    gray = cv.GaussianBlur(gray, (3, 3), 0)
    #show(gray, 'gray')


    ### Обработка

    # Распознавание контуров:
    ret, thresh = cv.threshold(gray, 100, 255, 0)
    #show(thresh, 'thresh')

    im2, contours, hierarchy = cv.findContours(thresh, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    edge_detected_image = cv.Canny(thresh, 75, 200)
    #show(edge_detected_image, 'edged')

    # Подсчет контуров:
    total = 0
    for c in contours:
        # аппроксимируем (сглаживаем) контур
        peri = cv.arcLength(c, True)
        approx = cv.approxPolyDP(c, 0.05, True)
        area = cv.contourArea(c)
        #если периметр больше, чем 300
        if (area > 10000) & (peri < (width+height)*2):
            # если больше 5 вершин
            if len(approx) > 5:
                cv.drawContours(img, [approx], -1, (0, 255, 0), 4)
                total += 1

    # Вывод:
    #show(img, 'result')
    return total

