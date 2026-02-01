var request = require('../../utils/request').request;
var checkLogin = require('../../utils/auth').checkLogin;

Page({
  data: {
    loading: true,
    currentYear: 2026,
    currentMonth: 2,
    checkinDates: {},
    stats: {
      consecutiveDays: 0,
      totalDays: 0
    },
    calendar: [],
    weekDays: ['日', '一', '二', '三', '四', '五', '六']
  },

  onLoad: function() {
    var now = new Date();
    this.setData({
      currentYear: now.getFullYear(),
      currentMonth: now.getMonth() + 1
    });
    console.log('打卡日历加载');
  },

  onShow: function() {
    if (!checkLogin()) {
      wx.navigateTo({ url: '/pages/login/index' });
      return;
    }
    this.loadCalendar();
  },

  loadCalendar: function() {
    var that = this;
    that.setData({ loading: true });

    request({
      url: '/students/me/checkin-history',
      data: {
        year: that.data.currentYear,
        month: that.data.currentMonth
      }
    }).then(function(res) {
      console.log('打卡记录:', res.data);
      
      that.setData({
        checkinDates: res.data.checkinDates || {},
        stats: res.data.currentStats || {
          consecutiveDays: 0,
          totalDays: 0
        },
        loading: false
      });
      
      that.generateCalendar();
    }).catch(function(err) {
      console.error('获取打卡记录失败:', err);
      that.setData({ loading: false });
    });
  },

  generateCalendar: function() {
    var year = this.data.currentYear;
    var month = this.data.currentMonth;
    var checkinDates = this.data.checkinDates;
    
    var firstDay = new Date(year, month - 1, 1);
    var lastDay = new Date(year, month, 0);
    var firstDayWeek = firstDay.getDay();
    var totalDays = lastDay.getDate();
    
    var calendar = [];
    var week = [];
    
    // 填充月初空白
    for (var i = 0; i < firstDayWeek; i++) {
      week.push({ day: '', checked: false, isToday: false });
    }
    
    // 填充日期
    var today = new Date();
    var todayStr = today.getFullYear() + '-' + 
                   String(today.getMonth() + 1).padStart(2, '0') + '-' + 
                   String(today.getDate()).padStart(2, '0');
    
    for (var day = 1; day <= totalDays; day++) {
      var dateStr = year + '-' + 
                    String(month).padStart(2, '0') + '-' + 
                    String(day).padStart(2, '0');
      
      week.push({
        day: day,
        date: dateStr,
        checked: !!checkinDates[dateStr],
        isToday: dateStr === todayStr
      });
      
      if (week.length === 7) {
        calendar.push(week);
        week = [];
      }
    }
    
    // 填充月末空白
    if (week.length > 0) {
      while (week.length < 7) {
        week.push({ day: '', checked: false, isToday: false });
      }
      calendar.push(week);
    }
    
    this.setData({ calendar: calendar });
  },

  prevMonth: function() {
    var month = this.data.currentMonth - 1;
    var year = this.data.currentYear;
    
    if (month < 1) {
      month = 12;
      year -= 1;
    }
    
    this.setData({
      currentYear: year,
      currentMonth: month
    });
    this.loadCalendar();
  },

  nextMonth: function() {
    var month = this.data.currentMonth + 1;
    var year = this.data.currentYear;
    
    if (month > 12) {
      month = 1;
      year += 1;
    }
    
    this.setData({
      currentYear: year,
      currentMonth: month
    });
    this.loadCalendar();
  },

  goToCheckin: function() {
    wx.switchTab({ url: '/pages/index/index' });
  }
});
