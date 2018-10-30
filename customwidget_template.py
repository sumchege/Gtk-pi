import gi
gi.require_version("Gtk", "3.0")
gi.require_version('PangoCairo', '1.0')
from gi.repository import GObject, Gtk, Gdk, cairo, Pango, PangoCairo
import math

bg_color_inv = (0.7, ) * 3
bg_color_gauge = (0.05, ) * 3
bg_color_bounderie = (0.1, ) * 3
bg_radial_color_begin_gauge = (0.7, ) * 3
bg_radial_color_begin_bounderie = (0.2, ) * 3

class customWidget(Gtk.DrawingArea):

    def __init__(self):
        Gtk.DrawingArea.__init__(self)
        self.set_size_request(200, 200)

        self.connect('draw', self.do_draw_cb)
    
    def do_draw_cb(self, widget, cr):
        # do staff
        pass 

class CircularGauge(Gtk.DrawingArea):

    def __init__(self):

        Gtk.DrawingArea.__init__(self)
        self.name = "CircularGauge"
        (self.min, self.max) = (0, 100)
        self.value = 0.0

        self.connect('draw', self.do_draw_cb)

    # Helper function for value 
    
    def set_value(self, value):
        if value > 100 or value < 0:
            print("Invalid value")
        else:
            self.value = value
            self.queue_draw()

    # Helper function for range transformation


    def value2angle(self, value): 
        return math.pi * (0.75 + 1.5 *value/ (self.max - self.min))
    
    def do_draw_cb(self, widget, cr):

        al = self.get_allocation()
        x = al.width / 2
        y = al.height / 2
        radius = min(x, y) 

        rec_x0 = x - radius
        rec_y0 = y - radius
        rec_width = radius * 2
        rec_height = radius * 2


        # Bacground rectangle

        cr.rectangle(0, 0, rec_width, rec_height)
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.9)
        cr.fill_preserve()
        cr.stroke()


        # Outer ring
 
        cr.arc(rec_width/2, rec_height/2, (radius - radius*0.08), 0, 2* math.pi)
        cr.set_line_width(0.015 * radius)
        cr.set_source_rgb(0.6, 0.6, 0.6)
        cr.stroke()


        # Inner color ring

        cr.set_line_width(radius*0.065)
        cr.arc(rec_width/2, rec_height/2, (radius - radius*0.12), 3/4*math.pi, 3/2* math.pi)
        cr.set_source_rgb(0.0, 0.8, 0.0)
        cr.stroke()

        cr.arc(rec_width/2, rec_height/2, (radius - radius*0.12), 3/2* math.pi, 0)
        cr.set_source_rgb(0.8, 0.8, 0.0)
        cr.stroke()

        cr.arc(rec_width/2, rec_height/2, (radius - radius*0.12), 0, math.pi/4)
        cr.set_source_rgb(0.8, 0.0, 0.0)
        cr.stroke()

        # Markers / Scales

        cr.set_source_rgb(1, 1, 1)
        # cr.set_line_width(0.015 * radius)

        for i in range(self.max + 1):
            cr.save()
            if i % 10 == 0:
                inset = 0.2
                cr.set_line_width(0.015 * radius)
            else:
                inset = 0.15
                cr.set_line_width(0.010 * radius)

            angle = math.pi * (0.75 + 0.015*i)

            rx1 = 0.9 * radius*math.cos(angle)
            ry1 = 0.9 * radius*math.sin(angle)

            rx2 = (1- inset)*radius*math.cos(angle)
            ry2 = (1- inset)*radius*math.sin(angle)


            cr.move_to(radius + rx1, radius + ry1)
            cr.line_to(radius + rx2, radius + ry2)
            cr.stroke()
            cr.restore()

        cr.set_source_rgb(1, 1, 1)
        cr.set_line_width(0.015 * radius)

        # Text/ Numbers

        for i in range(10 + 1):
            cr.save()
            inset = 0.28

            angle = math.pi * (0.75 + 0.015*i*10)

            rx2 = (1- inset)*radius*math.cos(angle)
            ry2 = (1- inset)*radius*math.sin(angle)
            cr.set_font_size(0.13 * radius)
            (tx, ty, tw, th, tdx, tdy) = cr.text_extents(str(i*10))
            cr.move_to(radius + rx2 - tw/2, radius + ry2 + th/2)
            cr.show_text(str(i*10))
            cr.stroke()
            cr.restore()

        # inner circle
        cr.set_source_rgb(1, 1, 1)
        cr.set_line_width(0.02 * radius)
        cr.arc(radius, radius, radius*0.05, 0, 2*math.pi)
        cr.stroke()

        # dynamic hand
        cr.set_source_rgb(1, 1, 1)
        cr.set_line_width(0.02 * radius)
        angle = self.value2angle(self.value)
        k = 0.22
        cr.move_to(radius, radius)
        cr.line_to(radius + (1 - k) * radius * math.cos(angle), radius + (1 -k) * radius * math.sin(angle))
        cr.move_to(radius, radius)
        k = 0.95
        cr.line_to(radius - (1 - k) * radius * math.cos(angle), radius - (1 -k) * radius * math.sin(angle))
        cr.stroke()


class LevelGaugeWidget(Gtk.DrawingArea):

    def __init__(self):
        Gtk.DrawingArea.__init__(self)
        self.value = 0.0
        self.h, self.w = (200, 200)
        self.min, self.max = (0, 100)
        self.mT, self.mL, self.mB  = (10, 85, 10)
        self.set_size_request(self.h, self.w)

        self.connect('draw', self.do_draw_cb)
    
    def set_value(self, newValue):
        if float(newValue) >= 100.0:
            self.value = 100.0
        elif float(newValue) <= 0:
            self.value = 0.0 
        else:
            self.value = float(newValue)
        self.queue_draw()
        print("Called")
    
    def transform_value(self, value):
        print("%f to %f", float(value), float( value * (self.h - self.mT - self.mB) / (self.max - self.min)))
        return float( value * (self.h - self.mT - self.mB) / (self.max - self.min))
        
    
    def do_draw_cb(self, widget, cr):
        # background
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.8)
        cr.rectangle(self.min, self.min, self.w, self.h)
        cr.fill()

        cr.set_source_rgba(1, 0.0, 0.2, 0.1)

        cr.rectangle(self.mL , (self.mT) , self.w - 2*self.mL, (self.h - self.mT - self.mB))
        cr.fill_preserve()
        cr.set_source_rgba(1, 0, 0.2, 0.8)
        cr.set_line_width(4)
        cr.stroke()

        cr.set_source_rgba(1, 0, 0.2, 0.8)
        y = self.mT + self.transform_value(self.max) - self.transform_value(self.value)
        h = self.h-self.mT - self.mB - self.transform_value(self.max) + self.transform_value(self.value)
        print(y, h)
        cr.rectangle(self.mL, y , self.w - 2*self.mL, h)
        cr.fill()



class RectWidget(Gtk.DrawingArea):

    def __init__(self):
        Gtk.DrawingArea.__init__(self)
        self.set_size_request(200, 200)

        self.connect('draw', self.do_draw_cb)
    
    def do_draw_cb(self, widget, cr):
        # background
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.8)
        cr.rectangle(0, 0, 200, 200)
        cr.fill()

        cr.set_source_rgba(1, 0.0, 0.2, 0.1)
        cr.arc(100, 100, 80, 0, 2*3.142)
        cr.fill_preserve()
        cr.set_source_rgba(1, 0, 0.2, 0.8)
        cr.set_line_width(5)
        cr.stroke()


        # center arc
        cr.set_source_rgba(1, 1, 0, 0.7)
        cr.arc(100, 100, 5, 0, 2*3.142)
        cr.fill()

        # arms
        cr.set_source_rgba(1, 1, 0, 0.8)
        cr.set_line_width(2)
        cr.move_to(100, 100)
        cr.line_to(100 + 70*math.cos(2), 100 + (-70)*math.sin(2))
        cr.stroke()

        # text
        layout = PangoCairo.create_layout (cr)
        cr.move_to(70, 130)
        cr.set_source_rgba(1, 1, 1, 0.8)
        layout.set_text("12.00 V", -1)
        desc = Pango.font_description_from_string ( "Courier Bold 12")
        layout.set_font_description( desc)
        PangoCairo.show_layout (cr, layout)

        # scales
        cr.set_source_rgba(1, 0, 0.2, 0.8)
        radius = 80
        for i in range(12):
            cr.save()
            if i % 3 == 0:
                inset = radius * .2
            else:
                inset = radius * .1
            
            cr.set_line_width(2)
            cr.move_to(100 + (radius - inset)*math.cos(math.pi * i/6), 100 + (-((radius - inset)))*math.sin(math.pi * i/6))
            cr.line_to(100 + (radius)*math.cos(math.pi * i/6), 100 + (-((radius)))*math.sin(math.pi * i/6))
            cr.stroke()
            cr.restore()



        
