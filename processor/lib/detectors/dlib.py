from face_recognition import face_locations

class DlibDetector(object):
    def __init__(self):
        pass
    def getBoxes(self, frame, model='cnn', boxes_to_return='box'):
        bboxes = face_locations(frame, model=model)
        if boxes_to_return == 'box':
            faces = []
            for (top, right, bottom, left) in bboxes:
                faces.append([left, top, right, bottom])
            bboxes = faces
        return bboxes