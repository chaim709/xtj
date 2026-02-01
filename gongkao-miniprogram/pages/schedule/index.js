var request = require('../../utils/request').request;
var checkLogin = require('../../utils/auth').checkLogin;
var formatDate = require('../../utils/util').formatDate;
var getToday = require('../../utils/util').getToday;
var getWeekRange = require('../../utils/util').getWeekRange;

Page({
  data: {
    loading: true,
    viewMode: 'day',
    currentDate: '',
    weekRange: null,
    schedules: [],
    weekDays: []
  },

  onLoad: function() {
    var today = getToday();
    var weekRange = getWeekRange();
    
    this.setData({
      currentDate: today,
      weekRange: weekRange
    });
    console.log('课表页加载, 当前日期:', today);
  },

  onShow: function() {
    if (!checkLogin()) {
      wx.navigateTo({ url: '/pages/login/index' });
      return;
    }
    this.loadSchedule();
  },

  onPullDownRefresh: function() {
    var that = this;
    that.loadSchedule();
    setTimeout(function() {
      wx.stopPullDownRefresh();
    }, 1500);
  },

  loadSchedule: function() {
    var that = this;
    that.setData({ loading: true });

    var params = {
      date: that.data.currentDate,
      week: that.data.viewMode === 'week' ? 'true' : 'false'
    };

    request({
      url: '/students/me/schedule',
      data: params
    }).then(function(res) {
      console.log('课表数据:', res.data);
      
      if (that.data.viewMode === 'week') {
        var grouped = that.groupByDate(res.data.schedules || []);
        that.setData({
          weekDays: grouped,
          schedules: res.data.schedules || [],
          loading: false
        });
      } else {
        that.setData({
          schedules: res.data.schedules || [],
          loading: false
        });
      }
    }).catch(function(err) {
      console.error('获取课表失败:', err);
      wx.showToast({ title: '获取课表失败', icon: 'none' });
      that.setData({ loading: false });
    });
  },

  groupByDate: function(schedules) {
    var map = {};
    var weekDates = this.getWeekDates();
    
    for (var i = 0; i < weekDates.length; i++) {
      var date = weekDates[i];
      map[date.date] = {
        date: date.date,
        day: date.day,
        dayNum: date.dayNum,
        isToday: date.isToday,
        schedules: []
      };
    }

    for (var j = 0; j < schedules.length; j++) {
      var s = schedules[j];
      if (map[s.date]) {
        map[s.date].schedules.push(s);
      }
    }

    var result = [];
    for (var key in map) {
      result.push(map[key]);
    }
    return result;
  },

  getWeekDates: function() {
    var result = [];
    var today = new Date(this.data.currentDate);
    var dayOfWeek = today.getDay() || 7;
    var monday = new Date(today);
    monday.setDate(today.getDate() - dayOfWeek + 1);

    var weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];

    for (var i = 0; i < 7; i++) {
      var date = new Date(monday);
      date.setDate(monday.getDate() + i);
      result.push({
        date: formatDate(date),
        day: weekDays[i],
        dayNum: date.getDate(),
        isToday: formatDate(date) === getToday()
      });
    }

    return result;
  },

  switchView: function(e) {
    var mode = e.currentTarget.dataset.mode;
    this.setData({ viewMode: mode });
    this.loadSchedule();
  },

  onDateChange: function(e) {
    this.setData({ currentDate: e.detail.value });
    this.loadSchedule();
  },

  prevDay: function() {
    var current = new Date(this.data.currentDate);
    var offset = this.data.viewMode === 'week' ? 7 : 1;
    current.setDate(current.getDate() - offset);
    this.setData({ currentDate: formatDate(current) });
    this.loadSchedule();
  },

  nextDay: function() {
    var current = new Date(this.data.currentDate);
    var offset = this.data.viewMode === 'week' ? 7 : 1;
    current.setDate(current.getDate() + offset);
    this.setData({ currentDate: formatDate(current) });
    this.loadSchedule();
  },

  goToday: function() {
    this.setData({ currentDate: getToday() });
    this.loadSchedule();
  }
});
