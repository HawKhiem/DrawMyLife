import cv2
import tkinter as tk

# Initialize tkinter
root = tk.Tk()
# Define a function to display the coordinates of the points clicked on the image
def click_event(event, x, y, flags, params):
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f'({x},{y},0),')

        # Put coordinates as text on the image
        # cv2.putText(img, f'({x},{y})', (x, y),
        #             cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Draw point on the image
        cv2.circle(img, (x, y), 3, (0, 255, 255), -1)

# Read the input image
img = cv2.imread('Lan4.jpg')

# Get the dimensions of the image
height, width, channels = img.shape
print(f'Original Image Size: Width={width}, Height={height}')

# Get screen resolution
screen_width = root.winfo_screenwidth()  # Replace with actual screen width
screen_height = root.winfo_screenheight()  # Replace with actual screen height

# Resize image if it's larger than the screen resolution while maintaining aspect ratio
if width > screen_width or height > screen_height:
    scaling_factor = min(screen_width / width, screen_height / height)
    new_width = int(width * scaling_factor)
    new_height = int(height * scaling_factor)
    img = cv2.resize(img, (new_width, new_height))
    print(f'Resized Image Size: Width={new_width}, Height={new_height}')

# Create a window
cv2.namedWindow('Point Coordinates', cv2.WINDOW_AUTOSIZE)

# Bind the callback function to window
cv2.setMouseCallback('Point Coordinates', click_event)

# Display the image
while True:
    cv2.imshow('Point Coordinates', img)
    k = cv2.waitKey(1) & 0xFF
    if k == 27:
        break

cv2.destroyAllWindows()
