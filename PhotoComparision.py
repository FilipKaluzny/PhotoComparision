# Libraries
from tkinter.constants import Y
from skimage.metrics import structural_similarity as compare_ssim
import ctypes
import imutils
import numpy as np
import cv2
import scipy.misc
import tkinter as tk
from tkinter.filedialog import askopenfilename
from PIL import ImageTk, Image
from goprocam import GoProCamera, constants

# Screen resolution, used to put images on cavas in right size
user32 = ctypes.windll.user32
screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
width = int(screensize[0]/3)
hight = (screensize[1]-300)

# Paths to basic photos used in GUI, you can add more photos like CADDY5_IMAGE or so
#and put them on scrollbar
LOGO = "./Images/logo.jfif"
CADDY5_IMAGE = "./Images/GOPR0502.JPG"
CADDY5MAXI_IMAGE = "./Images/GOPR0503.JPG"

# Basic photo reading function, return image in gray scale 
def ReadPhoto(PATH):
    photo = cv2.imread(PATH)
    photo = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY)
    return photo

# Another basic funcktion for photo reading, return image in BGR
def ReadFromList(PATH):
    photo = cv2.imread(PATH)
    return photo

# Takes photo on GoPro, downloands it, delete from camera and set at the left side of 
# GUI, GoPro must be turned on and have WiFi toggled on 
def TakePhotoGoPro():
    goproCamera = GoProCamera.GoPro()
    goproCamera.take_photo()
    goproCamera.downloadLastMedia (custom_filename='image_to_compare.JPG')
    path = "./image_to_compare.JPG"
    image_to_compare_raw = cv2.imread(path)
    goproCamera.delete("last")
    SetLeftPhoto(image_to_compare_raw)

# As the name says, it returns image in ImageTk format which is used on canvas in GUI, 
# somwhere there is a funcktion that alows you to convert ImageTk to OpenCV format
def PhotoResize(cv2_Photo,x,y):
    image = cv2.resize(cv2_Photo, (x,y))
    image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
    img =  ImageTk.PhotoImage(image = Image.fromarray(image))
    return img

# Opening image from file explorer, first photo
def OpenFileLeft():
    # File type
    filetypes = (
        ('PNG files', '*.png'),
        ('jpg files', '*.jpg*'),
        ('JPEG files', '*.JPEG')
        
        
    )
    # Show the open file dialog
    photo_source = askopenfilename(filetypes=filetypes)
    if(photo_source):
        photo = cv2.imread(photo_source)
        SetLeftPhoto(photo)

# Opening image from file explorer, second photo
def OpenFileMiddle():
    # File type
    filetypes = (
        ('PNG files', '*.png'),
        ('jpg files', '*.jpg*'),
        ('JPEG files', '*.JPEG')
        
    )
    # Show the open file dialog
    photo_source = askopenfilename(filetypes=filetypes)
    if(photo_source):
        photo = cv2.imread(photo_source)
        SetMiddlePhoto(photo)

# Resize both images and return them in gray scale
def Resize(FirstPhoto, SecondPhoto):
    FirstPhotoResized = cv2.resize(FirstPhoto, (width,hight))
    SecondPhotoResized = cv2.resize(SecondPhoto, (width,hight))

    FirstPhotoGray = cv2.cvtColor(FirstPhotoResized, cv2.COLOR_BGR2GRAY)
    SecondPhotoGray = cv2.cvtColor(SecondPhotoResized, cv2.COLOR_BGR2GRAY)

    return FirstPhotoGray, SecondPhotoGray

# Conversion from ImageTk to Open-Cv format
def pil_to_cv2(image):
    'PIL -> CV2'
    pil_image = ImageTk.getimage(image)
    pil_image_array = np.array(pil_image)
    cv2_image = cv2.cvtColor(pil_image_array, cv2.COLOR_RGB2BGR)

    return cv2_image

# Function that is responsible for rotating first picture to the second picture, you can watch 
# how it works in one of the videos that i left you link for in readme
def ORB(FirstPhoto, SecondPhoto):
    orb = cv2.ORB_create(10000)
    oryginal_kp,oryginal_des = orb.detectAndCompute(FirstPhoto, None)
    compared_kp,compared_des = orb.detectAndCompute(SecondPhoto, None)
    des_macher = cv2.DescriptorMatcher_create(cv2.DescriptorMatcher_BRUTEFORCE_HAMMING)

    matches = des_macher.match(oryginal_des,compared_des, None)
    matches = sorted(matches, key = lambda x:x.distance)

    points_from_oryginal = np.zeros((len(matches),2), dtype = np.float32)
    points_from_compared = np.zeros((len(matches),2), dtype = np.float32)

    for i, match in enumerate(matches):
        points_from_oryginal[i,:] = oryginal_kp[match.queryIdx].pt
        points_from_compared[i,:] = compared_kp[match.trainIdx].pt

    h, mask = cv2.findHomography(points_from_oryginal,points_from_compared, cv2.RANSAC)

    height, width = FirstPhoto.shape
    rotated_image = cv2.warpPerspective(FirstPhoto,h, (width,height))
    return rotated_image

# Computing the Structural Similarity Index (SSIM) between the two
# images, ensuring that the difference image is returned. The closer SSIM value
# is to 1, the better 
def SSIM(FirstPhoto, SecondPhoto):
    (score, diff) = compare_ssim(FirstPhoto, SecondPhoto, full=True)
    diff = (diff * 255).astype("uint8")
    return diff, score

# Draws keypoints on the two compared images, it shows where the differences are.
def DrawKeypointsFnc(diff, oryginal_image_resized, compared_image_resized):
    orb_temp = 120
    orb3 = cv2.ORB_create(orb_temp)
    kp_3,des_3 = orb3.detectAndCompute(diff, None)
    imageC = cv2.drawKeypoints(diff,kp_3,diff,None)

    for j in range (0,imageC.shape[0]):
        for i in range (0,imageC.shape[1]):
            if imageC [j, i][0] > 50 and imageC [j, i][1] > 50 and imageC [j, i][2] > 50:
                imageC [j, i] = [255,255,255]
    cv2.drawKeypoints(compared_image_resized,kp_3,compared_image_resized, color = (255,0,0))
    #cv2.drawKeypoints(oryginal_image_resized,kp_3,oryginal_image_resized, color = (255,0,0))
    return(oryginal_image_resized, compared_image_resized, imageC)

# GUI's basic photos 
logo_basic = ReadPhoto(LOGO)
caddy = ReadFromList(CADDY5_IMAGE)
caddy_maxi = ReadFromList(CADDY5MAXI_IMAGE)


#=================================================================TKINTER GUI==================================================================================

# Create object
root = tk.Tk()
# Fullscreen mode 
root.state('zoomed')


# Set title and logo on bar 
root.title('    ImageComp')
root.configure(background="#c0f7f7")
logo = ImageTk.PhotoImage(file = './Images/LOGO_VWP.png')
root.iconphoto(False, logo)

# Get screen width and height
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Set canvas
canvas = tk.Canvas(root, height=screen_height-500, width= screen_width-400)
canvas.grid(columnspan=3)

# Initial photos setup
left_photo = PhotoResize(logo_basic, int(screen_width/3),int(screen_height-300))
left_photo_label = tk.Label(image = left_photo)
left_photo_label.grid(column = 0, rowspan = 1, row = 0, sticky="N")

centre_photo = PhotoResize(logo_basic, int(screen_width/3),int(screen_height-300))
centre_photo_label = tk.Label(image = centre_photo)
centre_photo_label.grid(column = 1, rowspan = 1, row = 0, sticky="N")

right_photo = PhotoResize(logo_basic, int(screen_width/3),int(screen_height-300))
right_photo_label = tk.Label(image = right_photo)
right_photo_label.grid(column = 2, rowspan = 1, row = 0, sticky="N")




#Set all photos on canvas
def SetPhotos(image_1, image_2, image_3):
    global right_photo_label,centre_photo_label, left_photo_label, right_photo, centre_photo, left_photo

    left_photo = PhotoResize(image_1, int(screen_width/3),int(screen_height-300))
    left_photo_label = tk.Label(image = left_photo)
    left_photo_label.grid(column = 0, rowspan = 1, row = 0, sticky="N")


    centre_photo = PhotoResize(image_2, int(screen_width/3),int(screen_height-300))
    centre_photo_label_label = tk.Label(image = centre_photo)
    centre_photo_label_label.grid(column = 1, rowspan = 1, row = 0, sticky="N")

    right_photo = PhotoResize(image_3, int(screen_width/3),int(screen_height-300))
    right_photo_label = tk.Label(image = right_photo)
    right_photo_label.grid(column = 2, rowspan = 1, row = 0, sticky="N")

# Set only the left photos 
def SetLeftPhoto(image):
    global  left_photo, left_photo_label
    left_photo = PhotoResize(image, int(screen_width/3),int(screen_height-300))
    left_photo_label = tk.Label(image = left_photo)
    left_photo_label.grid(column = 0, rowspan = 1, row = 0, sticky="N")

# Set only the middle photo
def SetMiddlePhoto(image):
    global  centre_photo, centre_photo_label
    centre_photo = PhotoResize(image, int(screen_width/3),int(screen_height-300))
    centre_photo_label = tk.Label(image = centre_photo)
    centre_photo_label.grid(column = 1, rowspan = 1, row = 0, sticky="N")

# Main comparing function 
def Compare():
    global right_photo, centre_photo, left_photo
    left_photo_cv = pil_to_cv2(left_photo)
    centre_photo_cv = pil_to_cv2(centre_photo)
    right_photo_cv = pil_to_cv2(right_photo)
    left_photo_cv_gray, centre_photo_cv_gray = Resize(left_photo_cv, centre_photo_cv)
    rotated_image = ORB(left_photo_cv_gray,centre_photo_cv_gray)
    diff, score= SSIM(centre_photo_cv_gray, rotated_image)
    oryginal_image_resized, compared_image_resized, imageC = DrawKeypointsFnc(diff, left_photo_cv, centre_photo_cv)
    SSIM_text.set("SSIM: {0:.3}".format(score))
    SetPhotos(oryginal_image_resized, compared_image_resized, imageC)


# Scrollbar menu for the preset car selection, as i said you can add more 
def selected(event):
    global oryginal_image_resized, photo, photo_label, caddy
    if clicked.get() == "Caddy 5 Maxi":
        oryginal_image_resized = caddy_maxi
        SetLeftPhoto(oryginal_image_resized)
       
    if clicked.get() == "Caddy 5":
        oryginal_image_resized = caddy
        SetLeftPhoto(oryginal_image_resized)

options = [
    "Predefined photo",
    "Caddy 5 Maxi",
    "Transporter 6",
    "Crafter",
    "E-Crafter"
]
clicked = tk.StringVar()
clicked.set(options[0])
menu = tk.OptionMenu(root, clicked, *options, command=selected)
menu.grid(column = 2, rowspan = 1, row = 2, sticky="NWES")    


# Printing SSIM
SSIM_text = tk.StringVar()
SSIM_label = tk.Label(root,textvariable=SSIM_text, font = "Raleway" )
SSIM_text.set("SSIM: ")
SSIM_label.grid(column =2, row =1, sticky="NSWE")

# Comparision
compare_text = tk.StringVar()
compare_btn = tk.Button(root, textvariable=compare_text,command=Compare, font = "Raleway",
bg = "#66ff66", fg  = "white", height=1, width=15)
compare_text.set("Compare")
compare_btn.grid(column =1, row =1, sticky="NWE")

# Taking photo on GoPro 
compare_text = tk.StringVar()
compare_btn = tk.Button(root, textvariable=compare_text,command=TakePhotoGoPro, font = "Raleway",
bg = "#20bebe", fg  = "white", height=1, width=15)
compare_text.set("Take photo")
compare_btn.grid(column =0, row =1, sticky="NWE")

# First photo selection
first_photo_text = tk.StringVar()
first_photo_btn = tk.Button(root, textvariable=first_photo_text,command=OpenFileLeft, font = "Raleway", bg = "#20bebe", fg  = "white", height=1, width=15)
first_photo_text.set("Photo no. 1")
first_photo_btn.grid(column =0, row =2, sticky="NWE")

# Second photo selection
second_photo_text = tk.StringVar()
second_photo_btn = tk.Button(root, textvariable=second_photo_text,command=OpenFileMiddle, font = "Raleway", bg = "#20bebe", fg  = "white", height=1, width=15)
second_photo_text.set("Photo no. 2")
second_photo_btn.grid(column =1, row =2, sticky="NWE")


# Execute tkinter
root.mainloop()