import cv2
import numpy as np

# Define global variables
zoom_factor = 4
start_x, start_y = 0, 0
img = None  # Placeholder for the image

# Define a function to display the coordinates of the points clicked on the image
def click_event(event, x, y, flags, params):
    global zoom_factor, start_x, start_y

    if event == cv2.EVENT_LBUTTONDOWN:
        # Adjust coordinates based on zoom factor and current start positions
        adjusted_x = start_x + x // zoom_factor
        adjusted_y = start_y + y // zoom_factor
        print(f'({adjusted_x},{adjusted_y},0),')

        # Draw point on the full image
        cv2.circle(img, (adjusted_x, adjusted_y), 3, (0, 255, 255), -1)
        cv2.imshow('Point Coordinates', img)

def main():
    global img, zoom_factor, start_x, start_y

    # Read the input image
    img = cv2.imread('Lan5.jpg')
    height, width = img.shape[:2]

    # Create a window
    cv2.namedWindow('Point Coordinates')

    # Bind the callback function to window
    cv2.setMouseCallback('Point Coordinates', click_event)

    while True:
        # Calculate the region to zoom in
        zoom_width = width // zoom_factor
        zoom_height = height // zoom_factor
        end_x = min(start_x + zoom_width, width)
        end_y = min(start_y + zoom_height, height)

        # Extract the zoomed region from the image
        zoomed_img = img[start_y:end_y, start_x:end_x]

        # Calculate the actual size of the zoomed region to maintain aspect ratio
        actual_zoom_width = end_x - start_x
        actual_zoom_height = end_y - start_y

        # Resize the zoomed region
        display_img_resized = cv2.resize(zoomed_img, (width, height), interpolation=cv2.INTER_LINEAR)

        cv2.imshow('Point Coordinates', display_img_resized)
        k = cv2.waitKey(1) & 0xFF

        # Adjust the start_x and start_y based on the key pressed for zooming and panning
        if k == ord('w'):  # Pan up
            start_y = max(start_y - 10, 0)
        elif k == ord('s'):  # Pan down
            start_y = min(start_y + 10, height - zoom_height)
        elif k == ord('a'):  # Pan left
            start_x = max(start_x - 10, 0)
        elif k == ord('d'):  # Pan right
            start_x = min(start_x + 10, width - zoom_width)
        elif k == ord('z'):  # Zoom in
            zoom_factor = min(zoom_factor + 1, 8)  # Increase zoom level
        elif k == ord('x'):  # Zoom out
            zoom_factor = max(zoom_factor - 1, 1)  # Decrease zoom level
        elif k == 27:  # ESC key to exit
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
