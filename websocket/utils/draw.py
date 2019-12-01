import cv2

def drawYoloObjects(frame, results):

	frame_copy = frame.copy()

	for cat, score, bounds in results:
		left, top, right, bottom = bounds
		color = [102, 220, 225]
		cv2.rectangle(frame_copy, (left, top), (right, bottom), color, 1)
		text = "{}: {:.4f}".format(str(cat.decode("utf-8")), score)
		cv2.putText(frame_copy, text, (left, top), cv2.FONT_HERSHEY_COMPLEX, 0.5, color)

	return frame_copy

def drawFaces(frame, results, ids, names):
	frame_copy = frame.copy()
	color = [255, 0, 0]
	
	for i, box in enumerate(results):
		# left, top, right, bottom = box
		top, right, bottom, left = box
		cv2.rectangle(frame_copy, (left, top), (right, bottom), color, 2)
		cv2.putText(frame_copy, names[i], (left, top - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0, 0), 1, cv2.LINE_AA)
	return frame_copy

def drawCorners(frame, boxes):

	for bbox in boxes:

		x1, y1, x2, y2 = [int(c) for c in bbox]
		w = x2 - x1
		h = y2 - y1
		x = x1
		y = y1

		m = 0.2
		
		# Upper left corner
		pt1 = (x,y)
		pt2 = (int(x + m*w), y)
		cv2.line(frame, pt1, pt2, (255, 255, 0), 2, cv2.LINE_AA)

		pt1 = (x,y)
		pt2 = (x, int(y + m*h))
		cv2.line(frame, pt1, pt2, (255, 255, 0), 2, cv2.LINE_AA)

		# Upper right corner
		pt1 = (x + w, y)
		pt2 = (x + w, int(y + m*h))
		cv2.line(frame, pt1, pt2, (255, 255, 0), 2, cv2.LINE_AA)

		pt1 = (x + w, y)
		pt2 = (int(x + w - m * w), y)
		cv2.line(frame, pt1, pt2, (255, 255, 0), 2, cv2.LINE_AA)
		
		# Lower left corner
		pt1 = (x, y + h)
		pt2 = (x, int(y + h - m*h))
		cv2.line(frame, pt1, pt2, (255, 255, 0), 2, cv2.LINE_AA)

		pt1 = (x, y + h)
		pt2 = (int(x + m * w), y + h)
		cv2.line(frame, pt1, pt2, (255, 255, 0), 2, cv2.LINE_AA)
				
		# Lower right corner
		pt1 = (x + w, y + h)
		pt2 = (x + w, int(y + h - m*h))
		cv2.line(frame, pt1, pt2, (255, 255, 0), 2, cv2.LINE_AA)

		pt1 = (x + w, y + h)
		pt2 = (int(x + w - m * w), y + h)
		cv2.line(frame, pt1, pt2, (255, 255, 0), 2, cv2.LINE_AA)

	return frame