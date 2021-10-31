odoo.define(
  "user_access_right_alternative.DataManagerCustom",
  function (require) {
    "use strict";

    var DataManager = require("web.DataManager");
    var core = require("web.core");
    var rpc = require("web.rpc");
    var utils = require("web.utils");

    DataManager.include({
      /**
       * Loads various information concerning views: fields_view for each view,
       * the fields of the corresponding model, and optionally the filters.
       *
       * @param {Object} params
       * @param {String} params.model
       * @param {Object} params.context
       * @param {Array} params.views_descr array of [view_id, view_type]
       * @param {Object} [options] dictionary of various options:
       *     - options.load_filters: whether or not to load the filters,
       *     - options.action_id: the action_id (required to load filters),
       *     - options.toolbar: whether or not a toolbar will be displayed,
       * @return {Deferred} resolved with the requested views information
       */
      load_views: function (params, options) {
        console.log("Load View In Js Action#", params);
        var self = this;

        var model = params.model;
        var context = params.context;
        var views_descr = params.views_descr;
        var key = this._gen_key(model, views_descr, options || {}, context);
        if (params.model == "user.group.access.alternative") {
          console.log("Clear Cache>>>>>>>>>>");
          // Clear cache
          core.bus.trigger("clear_cache");
        }
        if (
          !this._cache.views[key] ||
          params.model == "user.group.access.alternative"
        ) {
          console.log("no cache..............");
          // Don't load filters if already in cache
          var filters_key;
          if (options.load_filters) {
            filters_key = this._gen_key(model, options.action_id);
            options.load_filters = !this._cache.filters[filters_key];
          }

          this._cache.views[key] = rpc
            .query({
              args: [],
              kwargs: {
                views: views_descr,
                options: options,
                context: context,
              },
              model: model,
              method: "load_views",
            })
            .then(function (result) {
              console.log("RES^^^^^^^^^^^^^^^", result);
              // Freeze the fields dict as it will be shared between views and
              // no one should edit it
              utils.deepFreeze(result.fields);

              // Insert views into the fields_views cache
              _.each(views_descr, function (view_descr) {
                var toolbar = options.toolbar && view_descr[1] !== "search";
                var fv_key = self._gen_key(
                  model,
                  view_descr[0],
                  view_descr[1],
                  toolbar,
                  context
                );
                var fvg = result.fields_views[view_descr[1]];
                fvg.viewFields = fvg.fields;
                fvg.fields = result.fields;
                self._cache.fields_views[fv_key] = $.when(fvg);
              });

              // Insert filters, if any, into the filters cache
              if (result.filters) {
                self._cache.filters[filters_key] = $.when(result.filters);
              }

              return result.fields_views;
            }, this._invalidate.bind(this, this._cache.views, key));
        }

        return this._cache.views[key];
      },
    });
  }
);
