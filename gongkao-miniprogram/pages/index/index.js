var request = require('../../utils/request').request;
var checkLogin = require('../../utils/auth').checkLogin;
var getToday = require('../../utils/util').getToday;

Page({
  data: {
    loading: true,
    refreshing: false,
    userInfo: null,
    todaySchedule: [],
    messages: [],
    pendingHomework: 0,
    checkinStats: {
      totalDays: 0,
      consecutiveDays: 0,
      todayChecked: false
    },
    today: ''
  },

  onLoad: function() {
    this.setData({ today: getToday() });
    console.log('首页加载, 今日:', this.data.today);
  },

  onShow: function() {
    if (!checkLogin()) {
      wx.navigateTo({ url: '/pages/login/index' });
      return;
    }
    this.loadData();
  },

  onPullDownRefresh: function() {
    var that = this;
    that.setData({ refreshing: true });
    that.loadData();
    setTimeout(function() {
      wx.stopPullDownRefresh();
      that.setData({ refreshing: false });
    }, 1500);
  },

  loadData: function() {
    var that = this;
    // 并行加载四个接口
    that.loadUserInfo();
    that.loadTodaySchedule();
    that.loadMessages();
    that.loadHomework();
  },

  loadUserInfo: function() {
    var that = this;
    request({ url: '/students/me' }).then(function(res) {
      console.log('用户信息:', res.data);
      that.setData({
        userInfo: res.data,
        checkinStats: res.data.checkinStats || {
          totalDays: 0,
          consecutiveDays: 0,
          todayChecked: false
        },
        loading: false
      });
    }).catch(function(err) {
      console.error('获取用户信息失败:', err);
      that.setData({ loading: false });
    });
  },

  loadTodaySchedule: function() {
    var that = this;
    request({
      url: '/students/me/schedule',
      data: { date: that.data.today }
    }).then(function(res) {
      console.log('今日课表:', res.data.schedules);
      that.setData({
        todaySchedule: res.data.schedules || []
      });
    }).catch(function(err) {
      console.error('获取课表失败:', err);
    });
  },

  loadMessages: function() {
    var that = this;
    request({
      url: '/students/me/messages',
      data: { limit: 3 }
    }).then(function(res) {
      console.log('督学消息:', res.data.items);
      that.setData({
        messages: res.data.items || []
      });
    }).catch(function(err) {
      console.error('获取消息失败:', err);
    });
  },

  loadHomework: function() {
    var that = this;
    request({
      url: '/students/me/homework'
    }).then(function(res) {
      console.log('作业列表:', res.data.items);
      var items = res.data.items || [];
      var pending = 0;
      for (var i = 0; i < items.length; i++) {
        if (items[i].status !== 'completed') {
          pending++;
        }
      }
      that.setData({ pendingHomework: pending });
    }).catch(function(err) {
      console.error('获取作业失败:', err);
    });
  },

  handleCheckin: function() {
    var that = this;
    if (that.data.checkinStats.todayChecked) {
      wx.showToast({ title: '今日已打卡', icon: 'none' });
      return;
    }

    request({
      url: '/students/me/checkin',
      method: 'POST',
      data: {}
    }).then(function(res) {
      console.log('打卡结果:', res);
      if (res.success) {
        var newStats = {
          todayChecked: true,
          totalDays: res.data.totalDays,
          consecutiveDays: res.data.consecutiveDays
        };
        that.setData({ checkinStats: newStats });
        wx.showToast({
          title: res.message || '打卡成功',
          icon: 'success'
        });
      }
    }).catch(function(err) {
      console.error('打卡失败:', err);
      wx.showToast({
        title: err.message || '打卡失败',
        icon: 'none'
      });
    });
  },

  goToMessages: function() {
    wx.navigateTo({ url: '/pages/messages/index' });
  },

  goToSchedule: function() {
    wx.switchTab({ url: '/pages/schedule/index' });
  },

  goToHomework: function() {
    wx.navigateTo({ url: '/pages/homework/index' });
  },

  goToCoze: function() {
    wx.navigateTo({ url: '/pages/coze/index' });
  }
});
