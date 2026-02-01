var request = require('../../utils/request').request;
var checkLogin = require('../../utils/auth').checkLogin;

Page({
  data: {
    loading: true,
    activeTab: 'pending',
    pendingList: [],
    completedList: []
  },

  onShow: function() {
    if (!checkLogin()) {
      wx.navigateTo({ url: '/pages/login/index' });
      return;
    }
    this.loadHomework();
  },

  onPullDownRefresh: function() {
    var that = this;
    that.loadHomework();
    setTimeout(function() {
      wx.stopPullDownRefresh();
    }, 1500);
  },

  loadHomework: function() {
    var that = this;
    that.setData({ loading: true });

    request({
      url: '/students/me/homework'
    }).then(function(res) {
      console.log('作业列表:', res.data.items);
      
      var pending = [];
      var completed = [];
      
      var items = res.data.items || [];
      for (var i = 0; i < items.length; i++) {
        // 格式化截止时间
        if (items[i].deadline) {
          items[i].deadlineFormatted = that.formatDeadline(items[i].deadline);
        }
        
        // 格式化提交时间
        if (items[i].submitTime) {
          items[i].submitTimeFormatted = that.formatDateTime(items[i].submitTime);
        }
        
        if (items[i].status === 'completed') {
          completed.push(items[i]);
        } else {
          pending.push(items[i]);
        }
      }
      
      that.setData({
        pendingList: pending,
        completedList: completed,
        loading: false
      });
    }).catch(function(err) {
      console.error('获取作业失败:', err);
      that.setData({ loading: false });
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
    });
  },

  formatDeadline: function(dateStr) {
    var date = new Date(dateStr);
    var month = date.getMonth() + 1;
    var day = date.getDate();
    var hour = date.getHours();
    var minute = date.getMinutes();
    
    return month + '月' + day + '日 ' + 
           (hour < 10 ? '0' + hour : hour) + ':' + 
           (minute < 10 ? '0' + minute : minute);
  },

  formatDateTime: function(dateStr) {
    var date = new Date(dateStr);
    var month = date.getMonth() + 1;
    var day = date.getDate();
    var hour = date.getHours();
    var minute = date.getMinutes();
    
    return month + '月' + day + '日 ' + 
           (hour < 10 ? '0' + hour : hour) + ':' + 
           (minute < 10 ? '0' + minute : minute);
  },

  switchTab: function(e) {
    var tab = e.currentTarget.dataset.tab;
    this.setData({ activeTab: tab });
  },

  viewDetail: function(e) {
    var id = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: '/pages/homework/detail?id=' + id
    });
  },

  markComplete: function(e) {
    var that = this;
    var id = e.currentTarget.dataset.id;
    
    wx.showModal({
      title: '确认',
      content: '确认已完成该作业？',
      success: function(res) {
        if (res.confirm) {
          that.submitHomework(id);
        }
      }
    });
  },

  submitHomework: function(id) {
    var that = this;
    
    wx.showLoading({
      title: '提交中...',
      mask: true
    });
    
    request({
      url: '/students/me/homework/' + id + '/complete',
      method: 'POST',
      data: {}
    }).then(function(res) {
      wx.hideLoading();
      wx.showToast({
        title: '提交成功',
        icon: 'success'
      });
      that.loadHomework();
    }).catch(function(err) {
      wx.hideLoading();
      console.error('提交失败:', err);
      var msg = '提交失败';
      if (err.error_code === 'ALREADY_SUBMITTED') {
        msg = '已提交过该作业';
      }
      wx.showToast({
        title: msg,
        icon: 'none'
      });
    });
  }
});
