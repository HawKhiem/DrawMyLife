# import the required library
import cv2
import numpy as np

# define a function to display the coordinates of the points clicked on the image
def click_event(event, x, y, flags, params):
    global zoom_factor, start_x, start_y

    if event == cv2.EVENT_LBUTTONDOWN:
        # Adjust coordinates based on zoom factor and current start positions
        adjusted_x = start_x + x // zoom_factor
        adjusted_y = start_y + y // zoom_factor
        print(f'({adjusted_x},{adjusted_y},0),')

        # Draw point on the full image
        cv2.circle(img, (adjusted_x, adjusted_y), 3, (0, 255, 255), -1)

# Initialize the zoom factor and start position
zoom_factor = 4
start_x, start_y = 0, 0

# Read the input image
img = cv2.imread('cat.png')
height, width = img.shape[:2]

# Create a window
cv2.namedWindow('Point Coordinates')

# Bind the callback function to window
cv2.setMouseCallback('Point Coordinates', click_event)

# Display the image
while True:
    # Calculate the region to zoom in
    end_x = min(start_x + width // zoom_factor, width)
    end_y = min(start_y + height // zoom_factor, height)
    zoomed_img = img[start_y:end_y, start_x:end_x]

    # Resize the zoomed region to the original image size for display
    display_img = cv2.resize(zoomed_img, (width, height))

    cv2.imshow('Point Coordinates', display_img)
    k = cv2.waitKey(1) & 0xFF

    # Adjust the start_x and start_y based on the key pressed for zooming and panning
    if k == ord('w'):  # Pan up
        start_y = max(start_y - 10, 0)
    elif k == ord('s'):  # Pan down
        start_y = min(start_y + 10, height - height // zoom_factor)
    elif k == ord('a'):  # Pan left
        start_x = max(start_x - 10, 0)
    elif k == ord('d'):  # Pan right
        start_x = min(start_x + 10, width - width // zoom_factor)
    elif k == ord('z'):  # Zoom in
        zoom_factor = min(zoom_factor + 1, 8)  # Increase zoom level
    elif k == ord('x'):  # Zoom out
        zoom_factor = max(zoom_factor - 1, 1)  # Decrease zoom level
    elif k == 27:  # ESC key to exit
        break

cv2.destroyAllWindows()
