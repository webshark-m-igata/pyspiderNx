// Vue.js 3 version of index.js
// Author: Augment Agent
// Created on 2024-04-18

// Main Vue application
document.addEventListener('DOMContentLoaded', function() {
  console.log('DOM Content Loaded');

  // Vue.js 3 global object check
  if (typeof window.Vue === 'undefined') {
    console.error('Vue is not defined. Make sure Vue.js 3 is loaded correctly.');
    return;
  }
  console.log('Vue version:', window.Vue.version);

  // Create Vue app
  const app = window.Vue.createApp({
    data() {
      // Initialize projects with default values
      const projects = window.projects || [];

      // Ensure all projects have the required properties
      projects.forEach(project => {
        // Initialize time property if not exists
        if (!project.time) {
          project.time = { fetch_time: 0, process_time: 0 };
        }

        // Initialize progress property if not exists
        if (!project.progress) {
          project.progress = {
            '5m': { pending: 0, success: 0, retry: 0, failed: 0, task: 0, title: '' },
            '1h': { pending: 0, success: 0, retry: 0, failed: 0, task: 0, title: '' },
            '1d': { pending: 0, success: 0, retry: 0, failed: 0, task: 0, title: '' },
            'all': { pending: 0, success: 0, retry: 0, failed: 0, task: 0, title: '' }
          };
        }
      });

      return {
        projects: projects
      };
    },

    mounted() {
      // Initialize editable fields
      this.initEditable();

      // Initialize sortable tables
      this.initSortable();

      // Start counter updates
      this.updateCounter();

      // Setup project creation form
      this.setupProjectForm();
    },
    methods: {
      project_run(project, event) {
        console.log('Run button clicked for project:', project.name);
        var $this = $(event.target);
        $this.addClass('btn-warning');

        // Check if project status is not RUNNING or DEBUG
        if (project.status !== 'RUNNING' && project.status !== 'DEBUG') {
          // Show alert
          $('#need-set-status-alert').fadeIn();
          // Remove warning class and add danger class
          $this.removeClass('btn-warning').addClass('btn-danger');
          setTimeout(function() {
            $this.removeClass('btn-danger');
          }, 1000);
          return;
        }

        $.ajax({
          type: "POST",
          url: "/run",
          data: {
            project: project.name
          },
          success: function(data) {
            console.log(data);
            $this.removeClass('btn-warning');
            if (data.result) {
              $this.addClass('btn-success');
              setTimeout(function() {
                $this.removeClass('btn-success');
              }, 1000);
            } else {
              $this.addClass('btn-danger');
              setTimeout(function() {
                $this.removeClass('btn-danger');
              }, 1000);
            }
          },
          error: function(xhr, textStatus, errorThrown) {
            console.log(xhr, textStatus, errorThrown);
            $this.removeClass('btn-warning');
            $this.addClass('btn-danger');
            setTimeout(function() {
              $this.removeClass('btn-danger');
            }, 1000);
          }
        });
      },

      initEditable() {
        // Initialize x-editable for project fields
        $(".project-group>span").editable({
          name: "group",
          pk: function() {
            return $(this).parents("tr").data("name");
          },
          emptytext: "[group]",
          placement: "right",
          url: "/update",
          success: (response, newValue) => {
            const projectName = $(this).parents("tr").data("name");
            this.projects[projectName].group = newValue;
            $(this).attr("style", "");
          }
        });

        $(".project-status>span").editable({
          type: "select",
          name: "status",
          source: [
            {value: "TODO", text: "TODO"},
            {value: "STOP", text: "STOP"},
            {value: "CHECKING", text: "CHECKING"},
            {value: "DEBUG", text: "DEBUG"},
            {value: "RUNNING", text: "RUNNING"}
          ],
          pk: function() {
            return $(this).parents("tr").data("name");
          },
          emptytext: "[status]",
          placement: "right",
          url: "/update",
          success: function(response, newValue) {
            const projectName = $(this).parents("tr").data("name");
            app.projects[projectName].status = newValue;
            $(this)
              .removeClass("status-" + $(this).attr("data-value"))
              .addClass("status-" + newValue)
              .attr("data-value", newValue)
              .attr("style", "");
          }
        });

        $(".project-rate>span").editable({
          name: "rate",
          pk: function() {
            return $(this).parents("tr").data("name");
          },
          validate: function(value) {
            var parts = value.split("/");
            if (parts.length != 2) {
              return "format error: rate/burst";
            }
            if (!$.isNumeric(parts[0]) || !$.isNumeric(parts[1])) {
              return "format error: rate/burst";
            }
          },
          highlight: false,
          emptytext: "0/0",
          placement: "right",
          url: "/update",
          success: function(response, newValue) {
            const projectName = $(this).parents("tr").data("name");
            const parts = newValue.split("/");
            app.projects[projectName].rate = parseFloat(parts[0]);
            app.projects[projectName].burst = parseFloat(parts[1]);
            $(this).attr("style", "");
          }
        });
      },

      initSortable() {
        Sortable.getColumnType = function(table, index) {
          var type = $($(table).find("th").get(index)).data("type");
          return type == "num" ? Sortable.types.numeric :
                 type == "date" ? Sortable.types.date :
                 Sortable.types.alpha;
        };

        $("table.projects").attr("data-sortable", true);
        Sortable.init();
      },

      updateCounter() {
        const updateCounters = () => {
          // Update project counters
          $.get("/counter", (data) => {
            for (let project in data) {
              const counter = data[project];
              if (this.projects[project] !== undefined) {
                const types = "5m,1h,1d,all".split(",");
                let needsUpdate = true;

                for (let i = 0; i < types.length; i++) {
                  const type = types[i];
                  if (counter[type] === undefined) {
                    needsUpdate = false;
                    break;
                  }
                }

                if (needsUpdate) {
                  for (let i = 0; i < types.length; i++) {
                    const type = types[i];
                    this.projects[project].progress[type] = counter[type];
                  }
                }
              }
            }
          });

          // Update queue information
          $.get("/queues", (data) => {
            for (let key in data) {
              $(".queue_value[title=\"" + key + "\"]").text(data[key]);
            }
          });

          setTimeout(updateCounters, 5000);
        };

        updateCounters();
      },

      setupProjectForm() {
        // Project creation form validation
        $(".project-create").on('click', function() {
          $("#create-project-modal").find(".has-error").removeClass("has-error");
          $("#create-project-modal").find(".help-block").hide();
        });

        $("#create-project-modal form").on('submit', function(ev) {
          var project_name = $(this).find("input[name=project-name]");
          if (project_name.val().search(/[^\w]/) != -1) {
            project_name.parents(".form-group").addClass("has-error");
            project_name.next(".help-block").show();
            ev.preventDefault();
            return false;
          }
          return true;
        });
      }
    }
  });

  // Mount the app to the body element to include header and section
  app.mount('body');
});
