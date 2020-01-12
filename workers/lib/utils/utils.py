def toOriginal(boxes, r):
    bboxes = []
    for (left, top, right, bottom) in boxes:
        left, top = int(left * r), int(top * r)
        right, bottom = int(right * r), int(bottom * r)
        bboxes.append([left, top, right, bottom])
    return bboxes