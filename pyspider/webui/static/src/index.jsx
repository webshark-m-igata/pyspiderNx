// vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
// Author: Binux<i@binux.me>
//         http://binux.me
// Created on 2014-03-02 17:53:23

import React from 'react';
import ReactDOM from 'react-dom';
import "./index.less";

// EditableField component for inline editing
class EditableField extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      editing: false,
      value: props.value || '',
      originalValue: props.value || ''
    };
    this.toggleEdit = this.toggleEdit.bind(this);
    this.handleChange = this.handleChange.bind(this);
    this.handleBlur = this.handleBlur.bind(this);
    this.handleKeyDown = this.handleKeyDown.bind(this);
  }

  componentDidUpdate(prevProps) {
    if (prevProps.value !== this.props.value) {
      this.setState({ value: this.props.value || '', originalValue: this.props.value || '' });
    }
  }

  toggleEdit() {
    this.setState(prevState => ({ editing: !prevState.editing }));
  }

  handleChange(e) {
    this.setState({ value: e.target.value });
  }

  handleBlur() {
    const { value, originalValue } = this.state;
    if (value !== originalValue) {
      this.props.onSave(value);
    }
    this.setState({ editing: false });
  }

  handleKeyDown(e) {
    if (e.key === 'Enter') {
      this.handleBlur();
    } else if (e.key === 'Escape') {
      this.setState({ value: this.state.originalValue, editing: false });
    }
  }

  render() {
    const { editing, value } = this.state;
    const { emptyText, className } = this.props;

    if (editing) {
      return (
        <input
          type="text"
          className="form-control form-control-sm"
          value={value}
          onChange={this.handleChange}
          onBlur={this.handleBlur}
          onKeyDown={this.handleKeyDown}
          autoFocus
        />
      );
    }

    return (
      <span className={className} onClick={this.toggleEdit}>
        {value || <em>{emptyText}</em>}
      </span>
    );
  }
}

// StatusSelect component for status editing
class StatusSelect extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      editing: false,
      value: props.value || '',
      originalValue: props.value || ''
    };
    this.toggleEdit = this.toggleEdit.bind(this);
    this.handleChange = this.handleChange.bind(this);
    this.handleBlur = this.handleBlur.bind(this);
  }

  componentDidUpdate(prevProps) {
    if (prevProps.value !== this.props.value) {
      this.setState({ value: this.props.value || '', originalValue: this.props.value || '' });
    }
  }

  toggleEdit() {
    this.setState(prevState => ({ editing: !prevState.editing }));
  }

  handleChange(e) {
    const value = e.target.value;
    this.setState({ value });
    this.props.onSave(value);
    this.setState({ editing: false });
  }

  handleBlur() {
    this.setState({ editing: false });
  }

  render() {
    const { editing, value } = this.state;
    const { className, dataValue } = this.props;
    const options = [
      { value: 'TODO', text: 'TODO' },
      { value: 'STOP', text: 'STOP' },
      { value: 'CHECKING', text: 'CHECKING' },
      { value: 'DEBUG', text: 'DEBUG' },
      { value: 'RUNNING', text: 'RUNNING' }
    ];

    if (editing) {
      return (
        <select
          className="form-select form-select-sm"
          value={value}
          onChange={this.handleChange}
          onBlur={this.handleBlur}
          autoFocus
        >
          {options.map(option => (
            <option key={option.value} value={option.value}>{option.text}</option>
          ))}
        </select>
      );
    }

    return (
      <span className={className} data-value={dataValue} onClick={this.toggleEdit}>
        {value}
      </span>
    );
  }
}

// Project component
class Project extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      project: props.project
    };
    this.projectRun = this.projectRun.bind(this);
    this.updateGroup = this.updateGroup.bind(this);
    this.updateStatus = this.updateStatus.bind(this);
    this.updateRate = this.updateRate.bind(this);
  }

  componentDidUpdate(prevProps) {
    if (this.props.project !== prevProps.project) {
      this.setState({ project: this.props.project });
    }
  }

  projectRun(event) {
    const { project } = this.state;
    $("#need-set-status-alert").hide();
    if (project.status !== "RUNNING" && project.status !== "DEBUG") {
      $("#need-set-status-alert").show();
    }

    const _this = event.target;
    $(_this).addClass("btn-warning");
    $.ajax({
      type: "POST",
      url: '/run',
      data: {
        project: project.name
      },
      success: function(data) {
        $(_this).removeClass("btn-warning");
        if (!data.result) {
          $(_this).addClass("btn-danger");
        }
      },
      error: function() {
        $(_this).removeClass("btn-warning").addClass("btn-danger");
      }
    });
  }

  updateGroup(value) {
    const { project } = this.state;
    $.ajax({
      type: "POST",
      url: '/update',
      data: {
        pk: project.name,
        name: 'group',
        value: value
      },
      success: (response) => {
        const updatedProject = { ...project, group: value };
        this.setState({ project: updatedProject });
        this.props.onProjectUpdate(project.name, updatedProject);
      }
    });
  }

  updateStatus(value) {
    const { project } = this.state;
    $.ajax({
      type: "POST",
      url: '/update',
      data: {
        pk: project.name,
        name: 'status',
        value: value
      },
      success: (response) => {
        const updatedProject = { ...project, status: value };
        this.setState({ project: updatedProject });
        this.props.onProjectUpdate(project.name, updatedProject);
      }
    });
  }

  updateRate(value) {
    const { project } = this.state;
    const s = value.split('/');
    if (s.length !== 2 || !$.isNumeric(s[0]) || !$.isNumeric(s[1])) {
      return "format error: rate/burst";
    }

    $.ajax({
      type: "POST",
      url: '/update',
      data: {
        pk: project.name,
        name: 'rate',
        value: value
      },
      success: (response) => {
        const updatedProject = {
          ...project,
          rate: parseFloat(s[0]),
          burst: parseFloat(s[1])
        };
        this.setState({ project: updatedProject });
        this.props.onProjectUpdate(project.name, updatedProject);
      }
    });
  }

  render() {
    const { project } = this.state;
    const types = "5m,1h,1d,all".split(',');

    return (
      <tr data-name={project.name}>
        <td className="project-group">
          <EditableField
            value={project.group}
            emptyText="[group]"
            onSave={this.updateGroup}
          />
        </td>
        <td className="project-name">
          <a href={`/debug/${project.name}`}>{project.name}</a>
        </td>
        <td className="project-status">
          <StatusSelect
            value={project.paused ? 'PAUSED' : project.status}
            dataValue={project.paused ? 'PAUSED' : project.status}
            className={`status-${project.paused ? 'PAUSED' : project.status}`}
            onSave={this.updateStatus}
          />
        </td>
        <td className="project-rate" data-value={project.rate}>
          <EditableField
            value={`${project.rate}/${project.burst}`}
            emptyText="0/0"
            onSave={this.updateRate}
          />
        </td>
        <td className="project-time" data-value={project.time && (project.time.fetch_time + project.time.process_time)}>
          {project.time && project.time.fetch_time &&
            <span>{(project.time.fetch_time * 1000).toFixed(1)}+{(project.time.process_time * 1000).toFixed(2)}</span>
          }
        </td>
        {types.map(type => (
          <td key={type}
              className={`project-progress progress-${type}`}
              title={project.progress && project.progress[type] && project.progress[type].title}
              data-value={project.progress && project.progress[type] && project.progress[type].task}>
            <div className="progress">
              <div className="progress-text">
                {type}
                {project.progress && project.progress[type] && project.progress[type].task > 0 &&
                  <span>: {project.progress[type].task}</span>
                }
              </div>
              {project.progress && project.progress[type] && (
                <>
                  <div className="progress-bar progress-pending"
                      style={{ width: `${project.progress[type].pending/project.progress[type].task*100}%` }}></div>
                  <div className="progress-bar progress-bar-success progress-success"
                      style={{ width: `${project.progress[type].success/project.progress[type].task*100}%` }}></div>
                  <div className="progress-bar progress-bar-warning progress-retry"
                      style={{ width: `${project.progress[type].retry/project.progress[type].task*100}%` }}></div>
                  <div className="progress-bar progress-bar-danger progress-failed"
                      style={{ width: `${project.progress[type].failed/project.progress[type].task*100}%` }}></div>
                </>
              )}
            </div>
          </td>
        ))}
        <td className="project-actions" data-value={project.updatetime}>
          <button className="project-run btn btn-outline-primary btn-sm" onClick={this.projectRun}>Run</button>
          <a className="btn btn-outline-secondary btn-sm ms-1" href={`/tasks?project=${project.name}`} target="_blank">Active Tasks</a>
          <a className="btn btn-outline-secondary btn-sm ms-1" href={`/results?project=${project.name}`} target="_blank">Results</a>
        </td>
      </tr>
    );
  }
}

// ProjectList component
class ProjectList extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      projects: props.projects
    };
    this.handleProjectUpdate = this.handleProjectUpdate.bind(this);
  }

  handleProjectUpdate(projectName, updatedProject) {
    this.setState(prevState => ({
      projects: {
        ...prevState.projects,
        [projectName]: updatedProject
      }
    }));
  }

  render() {
    const { projects } = this.state;
    return (
      <tbody>
        {Object.values(projects).map(project => (
          <Project
            key={project.name}
            project={project}
            onProjectUpdate={this.handleProjectUpdate}
          />
        ))}
      </tbody>
    );
  }
}

// Main app initialization
$(function() {
  // Initialize project data
  var projects_map = {};
  projects.forEach(function(p) {
    p.paused = false;
    p.time = {};
    p.progress = {};
    projects_map[p.name] = p;
  });

  // Render React component
  ReactDOM.render(
    <ProjectList projects={projects_map} />,
    document.querySelector('.projects tbody')
  );

  // Initialize editable fields
  function init_editable() {
    $(".project-group>span").editable({
      name: 'group',
      pk: function(e) {
        return $(this).parents('tr').data("name");
      },
      emptytext: '[group]',
      placement: 'right',
      url: "/update",
      success: function(response, value) {
        var project_name = $(this).parents('tr').data("name");
        projects_map[project_name].group = value;
        $(this).attr('style', '');
      }
    });

    $(".project-status>span").editable({
      type: 'select',
      name: 'status',
      source: [
        {value: 'TODO', text: 'TODO'},
        {value: 'STOP', text: 'STOP'},
        {value: 'CHECKING', text: 'CHECKING'},
        {value: 'DEBUG', text: 'DEBUG'},
        {value: 'RUNNING', text: 'RUNNING'}
      ],
      pk: function(e) {
        return $(this).parents('tr').data("name");
      },
      emptytext: '[status]',
      placement: 'right',
      url: "/update",
      success: function(response, value) {
        var project_name = $(this).parents('tr').data("name");
        projects_map[project_name].status = value;
        $(this).removeClass('status-'+$(this).attr('data-value')).addClass('status-'+value).attr('data-value', value).attr('style', '');
      }
    });

    $(".project-rate>span").editable({
      name: 'rate',
      pk: function(e) {
        return $(this).parents('tr').data("name");
      },
      validate: function(value) {
        var s = value.split('/');
        if (s.length != 2)
          return "format error: rate/burst";
        if (!$.isNumeric(s[0]) || !$.isNumeric(s[1]))
          return "format error: rate/burst";
      },
      highlight: false,
      emptytext: '0/0',
      placement: 'right',
      url: "/update",
      success: function(response, value) {
        var project_name = $(this).parents('tr').data("name");
        var s = value.split('/');
        projects_map[project_name].rate = parseFloat(s[0]);
        projects_map[project_name].burst = parseFloat(s[1]);
        $(this).attr('style', '');
      }
    });
  }

  function init_sortable() {
    // table sortable
    Sortable.getColumnType = function(table, i) {
      var type = $($(table).find('th').get(i)).data('type');
      if (type == "num") {
        return Sortable.types.numeric;
      } else if (type == "date") {
        return Sortable.types.date;
      }
      return Sortable.types.alpha;
    };
    $('table.projects').attr('data-sortable', true);
    Sortable.init();
  }

  $("#create-project-modal form").on('submit', function(ev) {
    var $this = $(this);
    var project_name = $this.find('[name=project-name]').val()
    if (project_name.length == 0 || project_name.search(/[^\w]/) != -1) {
      $this.find('[name=project-name]').parents('.form-group').addClass('has-error');
      $this.find('[name=project-name] ~ .help-block').show();
      return false;
    }
    var mode = $this.find('[name=script-mode]:checked').val();
    $this.attr('action', '/debug/'+project_name);
    return true;
  });

  function update_counters() {
    $.get('/counter', function(data) {
      for (let project in data) {
        var info = data[project];
        if (projects_map[project] === undefined)
          continue;

        // data inject
        var types = "5m,1h,1d,all".split(',');
        for (let type of types) {
          var d = info[type];
          if (d === undefined)
            continue;
          var pending = d.pending || 0,
            success = d.success || 0,
            retry = d.retry || 0,
            failed = d.failed || 0,
            sum = d.task || pending + success + retry + failed;
          d.task = sum;
          d.title = ""+type+" of "+sum+" tasks:\n"
            +(type == "all"
              ? "pending("+(pending/sum*100).toFixed(1)+"%): \t"+pending+"\n"
              : "new("+(pending/sum*100).toFixed(1)+"%): \t\t"+pending+"\n")
            +"success("+(success/sum*100).toFixed(1)+"%): \t"+success+"\n"
            +"retry("+(retry/sum*100).toFixed(1)+"%): \t"+retry+"\n"
            +"failed("+(failed/sum*100).toFixed(1)+"%): \t"+failed;
        }

        projects_map[project].paused = info['paused'];
        projects_map[project].time = info['5m_time'];
        projects_map[project].progress = info;
      }

      // Re-render React component with updated data
      ReactDOM.render(
        <ProjectList projects={projects_map} />,
        document.querySelector('.projects tbody')
      );

      // Re-initialize editable fields
      init_editable();
    });
  }

  function update_queues() {
    $.get('/queues', function(data) {
      $('.queue_value').each(function(i, e) {
        var attr = $(e).attr('title');
        if (data[attr] !== undefined) {
          $(e).text(data[attr]);
        } else {
          $(e).text('???');
        }
      });
    });
  }

  // Initialize UI
  init_editable();
  init_sortable();
  update_counters();
  window.setInterval(update_counters, 15*1000);
  update_queues();
  window.setInterval(update_queues, 15*1000);
});
