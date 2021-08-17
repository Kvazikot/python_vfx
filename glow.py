import os
import cv2
from scipy.interpolate import UnivariateSpline 
from matplotlib import gridspec
from matplotlib import pyplot as plt
import matplotlib.pylab as plt
import numpy as np
import random
import time


def gen_rand_lut():
    a = 64;
    b = 128;
    c = 200;
    d = random.randint(0,50);
    lut = spreadLookupTable([0, 64, 128, 256], [10, a+d, b+d, 256])
    return lut;



def spreadLookupTable(x, y):
  spline = UnivariateSpline(x, y)
  return spline(range(256))

increaseLookupTable = spreadLookupTable([0, 64, 128, 256], [0, 80, 100, 256])

def warmImage(image, lut=increaseLookupTable, ca_frame=0):
    red_channel, green_channel, blue_channel = cv2.split(image)
    #red_channel = cv2.LUT(red_channel, increaseLookupTable).astype(np.uint8)
    red_channel = np.zeros((red_channel.shape[0],red_channel.shape[1]), dtype=np.uint8)
    green_channel = cv2.LUT(green_channel, lut).astype(float) 
    red_channel = cv2.LUT(red_channel, lut).astype(float)
    #red_channel += 0.1*(ca_frame)
    red_channel = red_channel.astype(np.uint8)
    green_channel = green_channel.astype(np.uint8)
    return cv2.merge((red_channel, green_channel, blue_channel))
    


#gen_cos_image([200,200])
#cv2.waitKey(0)

def alpha_blending(foreground, background, alpha):
    # Read the images
    #foreground = cv2.imread("puppets.png")
    #background = cv2.imread("ocean.png")
    #alpha = cv2.imread("puppets_alpha.png")
    
    # Convert uint8 to float
    foreground = foreground.astype(float)
    background = background.astype(float)
    
    # Normalize the alpha mask to keep intensity between 0 and 1
    alpha = alpha.astype(float)/255
    
    # Multiply the foreground with the alpha matte
    foreground = cv2.multiply(alpha, foreground)
    
    # Multiply the background with ( 1 - alpha )
    background = cv2.multiply(1.0 - alpha, background)
    
    # Add the masked foreground and background.
    outImage = cv2.add(foreground, background)
    outImage = outImage.astype('uint8')

    return outImage;

def a_blend(foreground, background, a_channel):
  red_channel2, green_channel2, blue_channel2 = cv2.split(background)
  red_channel, green_channel, blue_channel = cv2.split(foreground)    
  red_channel = alpha_blending(red_channel, red_channel2, a_channel)
  green_channel = alpha_blending(green_channel, green_channel2, a_channel)
  blue_channel = alpha_blending(blue_channel, blue_channel2, a_channel)
  return  cv2.merge((red_channel, green_channel, blue_channel))   

def gen_cos_image(shape):
    a = np.linspace(-np.pi/2, np.pi/2, shape[1])
    y = np.cos(a)
    img = np.zeros([shape[0],shape[1],3])
    print(f'shape={shape}')
    #img[:,:,0] = y*64/255.0
    img[:,:,1] = y*255
    print(img[:,:,1])
    #img[:,:,2] = np.ones([5,5])*192/255.0
    #cv2.imshow("image", img)
    return img;
    #plt.plot(x, np.sin(x))
    #plt.xlabel('Angle [rad]')
    #plt.ylabel('sin(x)')
    #plt.axis('tight')
    #plt.show()

def rotate(image, angle, center = None, scale = 1.0):
    (h, w) = image.shape[:2]
    if center is None:
        center = (w / 2, h / 2)
    # Perform the rotation
    M = cv2.getRotationMatrix2D(center, angle, scale)
    rotated = cv2.warpAffine(image, M, (w, h))
    return rotated
  
def make_waves(freq_scaler, phaze, cols):
    freq_scaler = 2
    a = np.linspace(-freq_scaler*np.pi/2, freq_scaler*np.pi/2, cols)
    g = ((0.25+np.cos(2*a+phaze))/6 + 0.75) * 255   
    return g
    
def lines_vfx(x, a_channel, ca_frame, freq_scaler, phaze):
    rows = x.shape[0]
    z = x.copy()
    h_line = 5
    x_offset_max = 10
    n_rects = int(rows / h_line)
   

    
    if phaze!=0:
        for j in range(0, rows-h_line, h_line):        
            lut = gen_rand_lut()
            x_offset = random.randint(0,x_offset_max);
            y = x[j:j+h_line,0:x.shape[1]].copy()
            y[0:h_line, 0:x.shape[1]-x_offset] = y[0:h_line, x_offset:x.shape[1]].copy()
            blur = cv2.GaussianBlur(y, (0,0), random.random()*6);
            z[j:j+h_line,0:x.shape[1]] = warmImage(blur, lut, ca_frame[j:j+h_line,0:x.shape[1]])
            #make rects fade on the ends
            #a = np.linspace(-np.pi/2, np.pi/2, x.shape[1])
            #a_channel[j:j+h_line,0:x.shape[1]] = np.cos(a)*255
            #print(str(j) + " to " +  str(j+h_line));
    else:
      z = x
    return z, a_channel;        
    #y = x[30:100,0:x.shape[1]].copy()

def read_ca_frame(n_frame, shape):
    n_ca_frames = 7532
    if(n_frame > 7532):
       n_frame = (n_frame % 7532) 
    frame = cv2.imread(f'D:\\src\\live_gpu\\frames\\frame{n_frame+1}.png')
    frame = cv2.resize(frame, (shape[1], shape[0]))
    red_channel, green_channel, blue_channel  = cv2.split(frame)
    return 255 - green_channel;
    
def mix_ca(background, ca_frame, mask):
    red_channel, green_channel, blue_channel  = cv2.split(background)
    #red_channel2, green_channel2, blue_channel2  = cv2.split(ca_frame)
    green_channel = green_channel.astype(float)
    green_channel = np.where((mask==2)|(mask==0), ca_frame, green_channel).astype('uint8')
    #green_channel = (ca_frame )
    green_channel = green_channel.astype(np.uint8)
    return cv2.merge((red_channel, green_channel, blue_channel))   

def glow_vfx(frame, mask, background, phaze, fr, freq_scaler, enable_vfx):
    phaze += np.pi / 7;
    if fr%10 == 0:
        enable_vfx = not enable_vfx
    #a_channel = rotate(a_channel, 90)
    print(f'phaze={phaze}')        
    a_channel = np.where((mask==2)|(mask==0), 0, 255).astype('uint8')
    ca_frame = read_ca_frame(fr, a_channel.shape)
    # mix with background
    background = mix_ca(background, ca_frame, mask)
        
    #ca_frame = cv2.GaussianBlur(ca_frame, (0,0), 1.0);
    a_channel[:,:] = make_waves(freq_scaler, phaze, a_channel.shape[1])
    if enable_vfx:
        frame0, a_channel = lines_vfx(frame, a_channel, ca_frame, freq_scaler, phaze)
    else:
        frame0 = frame
    #frame0 = frame
    a_channel = np.where((mask==2)|(mask==0), 0, a_channel).astype('uint8')
    a_channel = cv2.GaussianBlur(a_channel, (0,0), 10.0);

        
    cv2.imshow("a_channel", a_channel)
    cv2.imshow("ca_frame", ca_frame)
    final = a_blend(frame0, background, a_channel)
    cv2.imshow('frame', final)
    

    return phaze, final, enable_vfx
    
def main_loop():
    background = cv2.imread('spaceship.jpg')
    frame = cv2.imread('image3_nobg.jpg')
    # for testing only
    background = cv2.imread('background.png')
    frame = cv2.imread('frame.png')
    mask_or = cv2.imread('mask.png')
    
    background = cv2.resize(background, (frame.shape[1], frame.shape[0]))
    gray = cv2.cvtColor(mask_or, cv2.COLOR_BGR2GRAY)
    mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)[1]
    kernel = np.ones((15, 15), np.uint8) 
    mask = cv2.erode(mask, kernel)
    mask_inv = cv2.bitwise_not(mask)
    a_channel = np.where((mask==2)|(mask==0), 0, 255).astype('uint8')
    
    mat_glow = warmImage(frame);

    
    #test of alpha blending
    print(a_channel.shape)
    print(frame.shape)
    print(background.shape)
    #frame, a_channel = lines_vfx(frame, a_channel, 2, 0)
    #final = a_blend(frame, background, a_channel)
    #cv2.imshow('final_blended', final)
    #cv2.waitKey(0)
   
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('glow.avi',fourcc, 20.0, (1280,960))
    
    #return;
    phaze = 0
    freq_scaler = 10
    enable_vfx = 1
    for fr in range(0,1,1):
        phaze, final, enable_vfx = glow_vfx(frame, mask, background, phaze, fr, freq_scaler, enable_vfx)
        time.sleep(0.05)
        final = cv2.resize(final, (1280,960))
        out.write(final)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            out.release()
    out.release()

#main_loop()