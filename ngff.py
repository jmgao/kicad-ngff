from __future__ import division
import pcbnew
import FootprintWizardBase

# Dimensions from PCIe M.2 Specification rev 1.0 §2.3.5.2.
keyingFirst = {
    "A": {
        "Q": 6.625,
        "R": 1.50,
        "S": 14.50,
        "T": 1.00,
        "U": 14.50,
        "PinMin": 8,
        "PinMax": 15,
    },
    "B": {
        "Q": 5.625,
        "R": 2.50,
        "S": 13.50,
        "T": 2.00,
        "U": 13.50,
        "PinMin": 12,
        "PinMax": 19,
    },
    "E": {
        "Q": 2.625,
        "R": 5.50,
        "S": 10.50,
        "T": 5.00,
        "U": 10.50,
        "PinMin": 24,
        "PinMax": 31,
    },
}

keyingSecond = {
    "M": {
        "V": 6.125,
        "W": 14.00,
        "X": 2.50,
        "Y": 1.00,
        "Z": 14.50,
        "PinMin": 59,
        "PinMax": 66,
    },
}

connectorHeight = pcbnew.FromMM(4.0)

connectorTotalWidth = pcbnew.FromMM(22.0)
connectorTongueWidth = pcbnew.FromMM(19.85)

connectorBaseArcRadius = pcbnew.FromMM(0.50)
connectorBaseLength = (connectorTotalWidth - connectorTongueWidth) / 2.0 - connectorBaseArcRadius;

padWidth = pcbnew.FromMM(0.35)
padPitch = pcbnew.FromMM(0.50)

# Pad heights include the vertical offset.
topPadHeight = pcbnew.FromMM(2.0)
bottomPadHeight = pcbnew.FromMM(2.50)
padVerticalOffset = pcbnew.FromMM(0.55)

topKeepout = pcbnew.FromMM(4.0)
bottomKeepout = pcbnew.FromMM(5.20)

keyDiameter = pcbnew.FromMM(1.20)
keyHeight = pcbnew.FromMM(3.50)

class NGFF_FootprintWizard(FootprintWizardBase.FootprintWizard):
    def GetName(self):
        return "NGFF (M.2) Edge Connector"

    def GetDescription(self):
        return "NGFF (M.2) Edge Connector Wizard"

    def GetValue(self):
        first = self.GetParam("Keying", "First").value
        second = self.GetParam("Keying", "Second").value
        if first:
            if second:
                return "NGFF_%s+%s" % (first, second)
            else:
                return "NGFF_%s" % first
        elif second:
            return "NGFF_%s" % second
        else:
            return "NGFF"

    def GenerateParameterList(self):
        self.AddParam("Keying", "First", self.uString, "B")
        self.AddParam("Keying", "Second", self.uString, "M")

    def firstKey(self):
        first = self.GetParam("Keying", "First").value
        return keyingFirst.get(first, None)

    def secondKey(self):
        second = self.GetParam("Keying", "Second").value
        return keyingSecond.get(second, None)

    def omitPin(self, number):
        firstKey = self.firstKey()
        if firstKey and firstKey["PinMin"] <= number <= firstKey["PinMax"]:
            return True

        secondKey = self.secondKey()
        if secondKey and secondKey["PinMin"] <= number <= secondKey["PinMax"]:
            return True

    def createPad(self, number, name):
        top = number % 2 == 1

        if self.omitPin(number):
            return None

        padTotalHeight = topPadHeight if top else bottomPadHeight
        padHeight = padTotalHeight - padVerticalOffset

        padSize = pcbnew.wxSize(padWidth, padHeight)

        padOneCenterX = pcbnew.FromMM(18 * 0.5 + 0.25)
        padTwoCenterX = padOneCenterX + pcbnew.FromMM(0.25)

        pad = pcbnew.D_PAD(self.module)

        layerSet = pcbnew.LSET()

        if top:
            # On the top, 0.0 is centered between pads 35 and 37.
            padOffset = (number - 1) / 2
            padCenterX = padOneCenterX - pcbnew.FromMM(padOffset * 0.5)
            layerSet.AddLayer(pcbnew.F_Cu)
        else:
            # On the bottom, 0.0 is the center of pad 36.
            padOffset = (number) / 2
            padCenterX = padTwoCenterX - pcbnew.FromMM(padOffset * 0.5)
            layerSet.AddLayer(pcbnew.B_Cu)

        padCenterY = -(padVerticalOffset + padHeight / 2.0)
        padCenter = pcbnew.wxPoint(padCenterX, padCenterY)

        pad.SetSize(padSize)
        pad.SetPos0(padCenter)
        pad.SetPosition(padCenter)
        pad.SetShape(pcbnew.PAD_SHAPE_RECT)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        pad.SetLayerSet(layerSet)
        pad.SetPadName(name)
        return pad

    def Arc(self, cx, cy, sx, sy, a):
        circle = pcbnew.EDGE_MODULE(self.module)
        circle.SetWidth(self.draw.dc['lineThickness'])

        center = self.draw.TransformPoint(cx, cy)
        start = self.draw.TransformPoint(sx, sy)

        circle.SetLayer(self.draw.dc['layer'])
        circle.SetShape(pcbnew.S_ARC)

        circle.SetAngle(a)
        circle.SetStartEnd(center, start)
        self.draw.module.Add(circle)

    def CheckParameters(self):
        first = self.GetParam("Keying", "First")
        second = self.GetParam("Keying", "Second")
        if first.value and first.value not in keyingFirst:
            msg = "Unknown first keying: %s (supported: %s)" % (first, ", ".join(sorted(keyingFirst.keys())))
            first.AddError(msg)

        if second.value and second.value not in keyingSecond:
            msg = "Unknown second keying: %s (supported: %s)" % (second, ", ".join(sorted(keyingSecond.keys())))
            second.AddError(msg)

    def FilledBox(self, x1, y1, x2, y2):
        box = pcbnew.EDGE_MODULE(self.module)
        box.SetShape(pcbnew.S_POLYGON);

        corners = pcbnew.wxPoint_Vector()
        corners.append(pcbnew.wxPoint(x1, y1))
        corners.append(pcbnew.wxPoint(x2, y1))
        corners.append(pcbnew.wxPoint(x2, y2))
        corners.append(pcbnew.wxPoint(x1, y2))

        box.SetPolyPoints(corners)
        return box

    def drawSolderMaskOpening(self, x1, x2, height, layer):
        rectCenterX = pcbnew.FromMM(0.0)
        rectCenterY = -height / 2.0
        
        box = self.FilledBox(x1, pcbnew.FromMM(0.0), x2, -height)
        box.SetLayer(layer)
        self.draw.module.Add(box)

    def BuildThisFootprint(self):
        draw = self.draw
        draw.SetLineThickness(pcbnew.FromMM(0.05))
        draw.Value(0, pcbnew.FromMM(2.0), self.GetTextSize())
        draw.Reference(0, pcbnew.FromMM(4.0), self.GetTextSize())

        draw.SetLayer(pcbnew.Edge_Cuts)
        centerX = centerY = pcbnew.FromMM(0.0)

        bottomEndpoints = []

        # Left base
        topLeftX = -connectorTotalWidth / 2.0
        topLeftY = -connectorHeight

        topLeftArcStartX = topLeftX + connectorBaseLength
        topLeftArcStartY = topLeftY

        draw.Line(topLeftX, topLeftY, topLeftArcStartX, topLeftY)

        topLeftArcCenterX = topLeftArcStartX
        topLeftArcCenterY = topLeftArcStartY + connectorBaseArcRadius
        topLeftArcAngle = 900 # decidegrees

        self.Arc(topLeftArcCenterX, topLeftArcCenterY, topLeftArcStartX, topLeftArcStartY, topLeftArcAngle)

        topLeftArcEndX = topLeftArcStartX + connectorBaseArcRadius
        topLeftArcEndY = topLeftArcStartY + connectorBaseArcRadius

        bottomLeftX = topLeftArcEndX
        bottomLeftY = topLeftArcEndY + connectorHeight - connectorBaseArcRadius

        bottomEndpoints.append(bottomLeftX)

        draw.Line(topLeftArcEndX, topLeftArcEndY, bottomLeftX, bottomLeftY)

        if self.secondKey():
            # Distance from the center of the footprint to the center of the key
            V = pcbnew.FromMM(self.secondKey()["V"])

            secondKeyBottomLeftX = centerX - V - keyDiameter / 2.0
            secondKeyBottomLeftY = centerY

            draw.Line(bottomLeftX, bottomLeftY, secondKeyBottomLeftX, secondKeyBottomLeftY)

            secondKeyTopLeftX = secondKeyBottomLeftX
            secondKeyTopLeftY = secondKeyBottomLeftY - keyHeight + keyDiameter / 2.0

            draw.Line(secondKeyBottomLeftX, secondKeyBottomLeftY, secondKeyTopLeftX, secondKeyTopLeftY)

            secondKeyCenterX = secondKeyTopLeftX + keyDiameter / 2.0
            secondKeyCenterY = secondKeyTopLeftY
            secondKeyArcAngle = 1800 # decidegrees

            self.Arc(secondKeyCenterX, secondKeyCenterY, secondKeyTopLeftX, secondKeyTopLeftY, secondKeyArcAngle)

            secondKeyTopRightX = secondKeyTopLeftX + keyDiameter
            secondKeyTopRightY = secondKeyTopLeftY

            secondKeyBottomRightX = secondKeyTopRightX
            secondKeyBottomRightY = centerY

            draw.Line(secondKeyTopRightX, secondKeyTopRightY, secondKeyBottomRightX, secondKeyBottomRightY)
            draw.Line(secondKeyBottomRightX, secondKeyBottomRightY, centerX, centerY)

            bottomEndpoints += [secondKeyBottomLeftX, secondKeyBottomRightX]
        else:
            draw.Line(bottomLeftX, bottomLeftY, centerX, centerY)

        # TODO: Implement the second key.

        bottomRightX = connectorTongueWidth / 2.0
        bottomRightY = centerY

        if self.firstKey():
            # Distance from the center of the footprint to the center of the key
            Q = pcbnew.FromMM(self.firstKey()["Q"])

            firstKeyBottomLeftX = centerX + Q - keyDiameter / 2.0
            firstKeyBottomLeftY = centerY
            
            draw.Line(centerX, centerY, firstKeyBottomLeftX, firstKeyBottomLeftY)

            firstKeyTopLeftX = firstKeyBottomLeftX
            firstKeyTopLeftY = firstKeyBottomLeftY - keyHeight + keyDiameter / 2.0

            draw.Line(firstKeyBottomLeftX, firstKeyBottomLeftY, firstKeyTopLeftX, firstKeyTopLeftY)

            firstKeyCenterX = firstKeyTopLeftX + keyDiameter / 2.0
            firstKeyCenterY = firstKeyTopLeftY
            firstKeyArcAngle = 1800 # decidegrees

            self.Arc(firstKeyCenterX, firstKeyCenterY, firstKeyTopLeftX, firstKeyTopLeftY, firstKeyArcAngle)

            firstKeyTopRightX = firstKeyTopLeftX + keyDiameter
            firstKeyTopRightY = firstKeyTopLeftY

            firstKeyBottomRightX = firstKeyTopRightX
            firstKeyBottomRightY = centerY

            draw.Line(firstKeyTopRightX, firstKeyTopRightY, firstKeyBottomRightX, firstKeyBottomRightY)
            draw.Line(firstKeyBottomRightX, firstKeyBottomRightY, bottomRightX, bottomRightY)

            bottomEndpoints += [firstKeyBottomLeftX, firstKeyBottomRightX]
        else:
            draw.Line(centerX, centerY, bottomRightX, bottomRightY)

        topRightArcStartX = bottomRightX
        topRightArcStartY = bottomRightY - connectorHeight + connectorBaseArcRadius

        bottomEndpoints.append(bottomRightX)

        draw.Line(bottomRightX, bottomRightY, topRightArcStartX, topRightArcStartY)

        topRightArcCenterX = topRightArcStartX + connectorBaseArcRadius
        topRightArcCenterY = topRightArcStartY
        topRightArcAngle = 900 # decidegrees

        self.Arc(topRightArcCenterX, topRightArcCenterY, topRightArcStartX, topRightArcStartY, topRightArcAngle)

        topRightArcEndX = topRightArcStartX + connectorBaseArcRadius
        topRightArcEndY = topRightArcStartY - connectorBaseArcRadius

        topRightX = connectorTotalWidth /2.0
        topRightY = -connectorHeight

        draw.Line(topRightArcEndX, topRightArcEndY, topRightX, topRightY)

        for endpoints in zip(bottomEndpoints[0::2], bottomEndpoints[1::2]):
            self.drawSolderMaskOpening(endpoints[0], endpoints[1], topPadHeight, pcbnew.F_Mask)
            self.drawSolderMaskOpening(endpoints[0], endpoints[1], bottomPadHeight, pcbnew.B_Mask)

        for padNumber in range(1, 76):
            pad = self.createPad(padNumber, str(padNumber))
            if pad:
                self.module.Add(pad)

NGFF_FootprintWizard().register()
