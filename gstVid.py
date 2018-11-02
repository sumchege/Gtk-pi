import os, sys 
import cairo
import gi
import datetime

gi.require_version("Gtk", "3.0")
gi.require_version("Gst", "1.0")
from gi.repository import Gtk
from gi.repository import Gst as Gst
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
gi.require_foreign('cairo')
from customwidget_template import CircularGauge

recordpipeline = None 

def main():
    builder = Gtk.Builder.new_from_file("gstVid.glade")
    window = builder.get_object("window")
    window.set_size_request(600, 600)
    window.set_title("Stream viewer")
    vidBox = builder.get_object("vidBox")
    button_play = builder.get_object("button_play")
    button_rec = builder.get_object("button_rec")

    # Build pipeline and extrack sink widget 
    Gst.init(None)
    pipeline = Gst.Pipeline.new("pipeline")
    # src = Gst.ElementFactory.make("ksvideosrc", "src")
    uridecodebin = Gst.ElementFactory.make("uridecodebin", "uridecodebin")
    vidconvert = Gst.ElementFactory.make("videoconvert", "videoconvert")
    audioconvert = Gst.ElementFactory.make("audioconvert", "audioconvert")
    overlay = Gst.ElementFactory.make("cairooverlay", "overlay")
    videoscale = Gst.ElementFactory.make("videoscale", "videoscale")
    tee = Gst.ElementFactory.make("tee", "tee")
    videoqueue = Gst.ElementFactory.make("queue", "videoqueue")
    gtksink = Gst.ElementFactory.make("gtksink", "gtksink")
    audiosink = Gst.ElementFactory.make("autoaudiosink", "audiosink")


    if(not pipeline or not uridecodebin or not vidconvert or not audioconvert or not overlay or not tee or not videoqueue or not gtksink or not audiosink):
        print("Error:  Not all gstreamer element could be created!")
        sys.exit(1)


    # reference to video output window
    video_widget = gtksink.props.widget
    vidBox.pack_start(video_widget, True, True, 0)

    # set up pipeline
    pipeline.add(uridecodebin)
    pipeline.add(vidconvert)
    pipeline.add(audioconvert)
    pipeline.add(overlay)
    pipeline.add(videoscale)
    pipeline.add(tee)
    pipeline.add(videoqueue)
    pipeline.add(gtksink)
    pipeline.add(audiosink)

    # set up recording pipeline
    def file_name():
        return datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S") + ".avi"


    def on_draw(_overlay, context, _timestamp, _duration):
        """Each time the 'draw' signal is emitted"""
        context.select_font_face('Open Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        context.set_font_size(20)
        context.move_to(0, 100)
        context.text_path('HELLO')
        context.set_source_rgb(0.5, 0.5, 1)
        context.fill_preserve()
        context.set_source_rgb(0, 0, 0)
        context.set_line_width(1)
        context.stroke()
    
    # Link pipeline elements
    # Note uridecode bin is not connected at first at codec discovery happens later


    if not audioconvert.link(audiosink):
        print("Error: Could not link audio conver to audio sink!")
        sys.exit(1)

    
    if not vidconvert.link(overlay):
        print("Error: Could not link video converter to overlay element!")
        sys.exit(1)

    if not overlay.link(videoscale):
        print("Error: Could not link to overlay to videoscale element")
        sys.exit(1) 

    if not videoscale.link(tee):
        print("Error: Could not link to videoscale to video sink element")
        sys.exit(1)  

    if not tee.link(videoqueue):
        print("Error: Could not link to videoscale to video sink element")
        sys.exit(1)    
    
    if not videoqueue.link(gtksink):
        print("Error: Could not link to videoscale to video sink element")
        sys.exit(1)    
    
    # get bus to monitor messages on the pipeline
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.enable_sync_message_emission()
    
    def on_pad_added(src, new_pad):
        print("Received new pad '{0:s}' from '{1:s}'".format(new_pad.get_name(), src.get_name()))

        # check pad type
        new_pad_caps = new_pad.get_current_caps()
        new_pad_struct = new_pad_caps.get_structure(0)
        new_pad_type = new_pad_struct.get_name()

        if new_pad_type.startswith("audio/x-raw"):
            sink_pad = audioconvert.get_static_pad("sink")
        elif new_pad_type.startswith("video/x-raw"):
            sink_pad = vidconvert.get_static_pad("sink")
        else:
            print("It has type '{0:s}' which is not raw audio/video. Ignoring".format(new_pad_type))
            return 
        
        # attempt linking, or ignore if connection exist
        if(sink_pad.is_linked()):
            print("Sink is linked. Ignoring..")
        
        # attempt link
        ret = new_pad.link(sink_pad)
        if(not ret == Gst.PadLinkReturn.OK):
            print("Type is of '{0:s}' but link failed".format(new_pad_type))
        else:
            print("Link succeded type('{0:s}')".format(new_pad_type))
        return

    # Handle pipeline bus message
    def on_message(bus, msg):
        t = msg.type
        if t == Gst.MessageType.EOS:
            pipeline.set_state(Gst.State.NULL)
            button_play.set_label("gtk-media-play")
            # print("EOS")
            
        if t == Gst.MessageType.ERROR:
            pipeline.set_state(Gst.State.NULL)
            error, debug = msg.parse_error()
            print("Error: %s", error, debug)
    
    def on_sync_msg(bus, msg):
        if msg.get_structure is None:
            return True
        
        if msg == "prepare-window-handle":
            gtksink.set_property("force-aspect-ratio", True)
            

        
    overlay.connect('draw', on_draw)
    uridecodebin.connect('pad-added', on_pad_added)
    bus.connect("message", on_message)
    bus.connect('sync-message::element',on_sync_msg)


    

    uri="rtsp://184.72.239.149/vod/mp4:BigBuckBunny_175k.mov"
    ure = "http://91.225.160.5:8080/Apple/112/.m3u8"
    uridecodebin.set_property("uri", uri)

    def start_recording():
        global recordpipeline

        filename = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S") + ".avi"
        recordpipeline = Gst.parse_bin_from_description("queue name=filequeue ! jpegenc ! avimux ! filesink location=" + filename, True)
        pipeline.add(recordpipeline)
        pipeline.get_by_name("tee").link(recordpipeline)
        recordpipeline.set_state(Gst.State.PLAYING)
    
    def probe_block(pad, buff):
        print("record pipe blocked")
        return True
    
    def stop_recording():
        global recordpipeline

        filequeue = recordpipeline.get_by_name("filequeue")
        filequeue.get_static_pad("src").add_probe(Gst.PadProbeType.BLOCK_DOWNSTREAM, probe_block)
        pipeline.get_by_name("tee").unlink(recordpipeline)
        filequeue.get_static_pad("sink").send_event(Gst.Event.new_eos())

        recordpipeline = None 
        print("Stopped recording")

    def play(args):
        label = button_play.get_label()
        if label == "gtk-media-play":
            pipeline.set_state(Gst.State.PLAYING)
            button_play.set_label("gtk-media-pause")
            print("playing " + uridecodebin.get_property("uri"))

        elif label == "gtk-media-pause":
            pipeline.set_state(Gst.State.PAUSED)
            button_play.set_label("gtk-media-play")
            print("paused..")
        else: 
            pass 

    def record(args):
        label = button_rec.get_label()
        if label == "gtk-media-record":
            start_recording()
            button_rec.set_label("gtk-media-stop")       
        else:
            stop_recording()
            button_rec.set_label("gtk-media-record")


    # print("recording..")
    
    button_play.connect('clicked', play)
    button_rec.connect('clicked', record)

    window.connect('destroy', lambda w: Gtk.main_quit())
    window.show_all()

    Gtk.main()


if __name__ == '__main__':
    main()
