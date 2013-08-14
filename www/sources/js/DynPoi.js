/* Copyright (c) 2006-2008 MetaCarta, Inc., published under a modified BSD license.
 * See http://svn.openlayers.org/trunk/openlayers/repository-license.txt 
 * for the full text of the license. */

/*
 * modified by Harald Kleiner, 2009-02-05
 * expanded text format with new columns specific to keepright
 * created special content inside the bubbles
 */

/*
 * modified by Etienne Chove, 2009-06-12
 * merge some files and simplify functions
 */

/*
 * modified by Nicolas Bouthors, 2009-06-23
 * permalink update
 */

OpenLayers.Format.DynPoiFormat = OpenLayers.Class(OpenLayers.Format, {

    initialize: function(options) {
        OpenLayers.Format.prototype.initialize.apply(this, [options]);
    }, 

    read: function(text) {
        var lines = text.split('\n');
        var columns;
        var features = [];
        for (var lcv = 0; lcv < (lines.length - 1); lcv++) {
            var currLine = lines[lcv].replace(/^\s*/,'').replace(/\s*$/,'');

            if (!columns) {
                //First line is columns
                columns = currLine.split('\t');
            } else {
                var vals = currLine.split('\t');
                var geometry = new OpenLayers.Geometry.Point(0,0);
                var attributes = {};
                var style = {};
                var icon, iconSize, iconOffset, overflow;
                var set = false;
                for (var valIndex = 0; valIndex < vals.length; valIndex++) {
                    if (vals[valIndex]) {
                        if (columns[valIndex] == 'lat') {
                            geometry.y = parseFloat(vals[valIndex]);
                            attributes['lat'] = geometry.y;
                            set = true; }
       			else if (columns[valIndex] == 'lon') {
                            geometry.x = parseFloat(vals[valIndex]);
                            attributes['lon'] = geometry.x;
                            set = true; }
                        else if (columns[valIndex] == 'image' || columns[valIndex] == 'icon')
                            style['externalGraphic'] = vals[valIndex];
                        else if (columns[valIndex] == 'iconSize') {
                            var size = vals[valIndex].split(',');
                            style['graphicWidth'] = parseFloat(size[0]);
                            style['graphicHeight'] = parseFloat(size[1]); } 
                        else if (columns[valIndex] == 'iconOffset') {
                            var offset = vals[valIndex].split(',');
                            style['graphicXOffset'] = parseFloat(offset[0]);
                            style['graphicYOffset'] = parseFloat(offset[1]); } 
                        else if (columns[valIndex] == 'marker_id')
                            attributes['marker_id'] = vals[valIndex];
                        else if (columns[valIndex] == 'html')
                            attributes['html'] = vals[valIndex];
                    }
                }
                if (set) {
                    if (this.internalProjection && this.externalProjection) {
                    geometry.transform(this.externalProjection, this.internalProjection); 
                }
                var feature = new OpenLayers.Feature.Vector(geometry, attributes, style);
                    features.push(feature);
                }
            }
        }
    return features;
    },

    CLASS_NAME: "OpenLayers.Format.DynPoiFormat"
    
});

OpenLayers.Layer.DynPoi = OpenLayers.Class(OpenLayers.Layer.Markers, {
    
    location:null,
    features: null,
    formatOptions: null, 
    selectedFeature: null,
    activePopup: null,
    activeFeature: null,
    clicked: false,
    marker_ids: {},

    initialize: function(name, options) {
        OpenLayers.Layer.Markers.prototype.initialize.apply(this, arguments);
        this.features = new Array();
    },

    destroy: function() {
        OpenLayers.Layer.Markers.prototype.destroy.apply(this, arguments);
        this.clearFeatures();
        this.features = null;
    },

    loadText: function() {
        if (this.location != null) {
            
	    
            var poiloc = this.location;

            var onFail = function(e) {
                this.events.triggerEvent("loadend");
            };

            this.events.triggerEvent("loadstart");

            OpenLayers.Request.GET({
                url: poiloc,
                success: this.parseData,
                failure: onFail,
                scope: this
            });
            
            this.loaded = true;
            
        }
    },

    moveTo:function(bounds, zoomChanged, minor) {
        OpenLayers.Layer.Markers.prototype.moveTo.apply(this, arguments);
        if(this.visibility && !this.loaded){
            this.loadText();
        }
    },

    parseData: function(ajaxRequest) {
    
        function create_markerbubble_feature(thisObject,feature) {
	    var data = {};
            var location;
            var iconSize, iconOffset;

            location = new OpenLayers.LonLat(feature.geometry.x, feature.geometry.y);

            if (feature.style.graphicWidth && feature.style.graphicHeight) {
                iconSize = new OpenLayers.Size(feature.style.graphicWidth, feature.style.graphicHeight);
            }

            // FIXME: At the moment, we only use this if we have an 
            // externalGraphic, because icon has no setOffset API Method.
            /**
            * FIXME FIRST!!
            * The Text format does all sorts of parseFloating
            * The result of a parseFloat for a bogus string is NaN.        That
            * means the three possible values here are undefined, NaN, or a
            * number.        The previous check was an identity check for null.        This
            * means it was failing for all undefined or NaN.        A slightly better
            * check is for undefined.        An even better check is to see if the
            * value is a number (see #1441).
      */
	    if (feature.style.graphicXOffset !== undefined && feature.style.graphicYOffset !== undefined) {
                iconOffset = new OpenLayers.Pixel(feature.style.graphicXOffset, feature.style.graphicYOffset);
            }

            if (feature.style.externalGraphic != null) {
                data.icon = new OpenLayers.Icon(feature.style.externalGraphic, iconSize, iconOffset);
            } else {
                data.icon = OpenLayers.Marker.defaultIcon();
                //allows for the case where the image url is not 
                // specified but the size is. use a default icon
                // but change the size
                if (iconSize != null) {
                    data.icon.setSize(iconSize);
                }
            }

            if (feature.attributes.comment == null) feature.attributes.comment="";
            if (feature.attributes.marker_id != null) {
                data['popupContentHTML'] = feature.attributes.html;
            }

            data['overflow'] = feature.attributes.overflow || "auto";
	    data.marker_id = feature.attributes.marker_id;

            var markerFeature = new OpenLayers.Feature(thisObject, location, data);
            markerFeature.popupClass=OpenLayers.Class(OpenLayers.Popup.FramedCloud);

            thisObject.features.push(markerFeature);
            var marker = markerFeature.createMarker();
            if (feature.attributes.marker_id != null) {
                marker.events.register("mousedown",markerFeature,thisObject.onClickHandler);
                marker.events.register("mouseover",markerFeature,thisObject.onHOverHandler);
                marker.events.register("mouseout",markerFeature,thisObject.onOutHandler);
            }
            thisObject.addMarker(marker);
            return markerFeature.id;
        }

        var text = ajaxRequest.responseText;

        var options = {};

        OpenLayers.Util.extend(options, this.formatOptions);

        if (this.map && !this.projection.equals(this.map.getProjectionObject())) {
            options.externalProjection = this.projection;
            options.internalProjection = this.map.getProjectionObject();
        }

        var parser = new OpenLayers.Format.DynPoiFormat(options);
        var features = parser.read(text);
        var newfeatures = {};
        var marker_id;
        for (var i=0, len=features.length; i<len; i++) {
            marker_id=features[i].attributes.marker_id;
            if (marker_id != undefined && marker_id != null) {
                if (!this.marker_ids[marker_id]) {
                    this.marker_ids[marker_id] = create_markerbubble_feature(this, features[i]);
                }
                newfeatures[marker_id]=true;
            }
        }

        // now remove features not needed any more
        var feature_id = null;
        for (var i in this.marker_ids) {
            if (!newfeatures[i]) {
                //console.log("dropping marker id " + i + " " + this.marker_ids[i]);
                feature_id=this.marker_ids[i];
                var featureToDestroy = null;
                var j=0;
                var len=this.features.length;
                while (j<len && featureToDestroy==null) {
                    if (this.features[j].id == feature_id) {
                        featureToDestroy=this.features[j];
                    }
                    j++;
                }
                if (featureToDestroy != null) {
		    OpenLayers.Util.removeItem(this.features, featureToDestroy);
                    // the marker associated to the feature has to be removed from map.markers manually
                    var markerToDestroy = null;
                    var k=0;
                    var len=this.markers.length;
                    while (k<len && markerToDestroy==null) {
                        if (this.markers[k].events.element.id == featureToDestroy.marker.events.element.id) {
                             markerToDestroy=this.markers[k];
                        }
                        k++;
                    }
                    OpenLayers.Util.removeItem(this.markers, markerToDestroy);
                    featureToDestroy.destroy();
                    featureToDestroy=null;
                }
                delete this.marker_ids[i];
            }
        }

        this.events.triggerEvent("loadend");
	
    },

    onClickHandler: function (evt) {
        this.activeFeature=this;
        if (this.clicked && this.activePopup==this.popup) {
            this.activePopup.hide();
            this.clicked=false;
        } else if ((this.clicked && !this.activePopup==this.popup) || !this.clicked) {
            if (this.activePopup!=null) {
                this.activePopup.hide();
            }
            if (this.popup==null) {
                this.popup=this.createPopup();
                this.popup.autoSize=true;
                this.popup.panMapIfOutOfView=false;//document.myform.autopan.checked;
                //this.popup.setSize(new OpenLayers.Size(280, 300));
                map.addPopup(this.popup);
            } else {
                this.popup.toggle();
            }
            this.activePopup=this.popup;
            this.clicked=true;
        }
        OpenLayers.Event.stop(evt);
    },

    onHOverHandler: function (evt) {
        if (!this.clicked) {
            if (this.activePopup!=null) {
                this.activePopup.hide();
            }
            if (this.popup==null) {
                this.popup=this.createPopup();
                this.popup.autoSize=true;
                this.popup.panMapIfOutOfView=false;//document.myform.autopan.checked;
                //this.popup.setSize(new OpenLayers.Size(280, 150));
                map.addPopup(this.popup);
            } else {
                this.popup.toggle();
            }
            this.activePopup=this.popup;
        }
        OpenLayers.Event.stop(evt);
    },

    onOutHandler: function (evt) {
        if (!this.clicked && this.activePopup!=null) this.activePopup.hide();
        OpenLayers.Event.stop(evt);
    },

    clearFeatures: function() {
        if (this.features != null) {
            while(this.features.length > 0) {
                var feature = this.features[0];
                OpenLayers.Util.removeItem(this.features, feature);
                feature.destroy();
            }
        }
    },

    CLASS_NAME: "OpenLayers.Layer.DynPoi"

});
