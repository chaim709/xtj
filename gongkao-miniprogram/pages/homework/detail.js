var request = require('../../utils/request').request;
var checkLogin = require('../../utils/auth').checkLogin;

Page({
  data: {
    loading: true,
    taskId: null,
    detail: null,
    isSubmitted: false
  },

  onLoad: function(options) {
    if (!checkLogin()) {
      wx.navigateTo({ url: '/pages/login/index' });
      return;
    }
    
    if (options.id) {
      this.setData({ taskId: options.id });
      this.loadDetail();
    }
  },

  loadDetail: function() {
    var that = this;
    that.setData({ loading: true });

    request({
      url: '/students/me/homework/' + that.data.taskId
    }).then(function(res) {
      console.log('作业详情:', res.data);
      
      var detail = res.data;
      
      // 格式化时间
      if (detail.deadline) {
        detail.deadlineFormatted = that.formatDateTime(detail.deadline);
      }
      if (detail.publishTime) {
        detail.publishTimeFormatted = that.formatDateTime(detail.publishTime);
      }
      if (detail.submission && detail.submission.submitTime) {
        detail.submission.submitTimeFormatted = that.formatDateTime(detail.submission.submitTime);
      }
      
      that.setData({
        detail: detail,
        isSubmitted: detail.submission && detail.submission.submitted,
        loading: false
      });
    }).catch(function(err) {
      console.error('获取作业详情失败:', err);
      that.setData({ loading: false });
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
    });
  },

  formatDateTime: function(dateStr) {
    var date = new Date(dateStr);
    var year = date.getFullYear();
    var month = date.getMonth() + 1;
    var day = date.getDate();
    var hour = date.getHours();
    var minute = date.getMinutes();
    
    return year + '年' + month + '月' + day + '日 ' + 
           (hour < 10 ? '0' + hour : hour) + ':' + 
           (minute < 10 ? '0' + minute : minute);
  },

  submitHomework: function() {
    var that = this;
    
    wx.showModal({
      title: '确认提交',
      content: '确认已完成该作业？',
      success: function(res) {
        if (res.confirm) {
          wx.showLoading({
            title: '提交中...',
            mask: true
          });
          
          request({
            url: '/students/me/homework/' + that.data.taskId + '/complete',
            method: 'POST',
            data: {}
          }).then(function(res) {
            wx.hideLoading();
            wx.showToast({
              title: '提交成功',
              icon: 'success'
            });
            
            setTimeout(function() {
              wx.navigateBack();
            }, 1500);
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
      }
    });
  }
});
