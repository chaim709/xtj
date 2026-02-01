var app = getApp();

var request = function(options) {
  return new Promise(function(resolve, reject) {
    var token = wx.getStorageSync('token');
    
    wx.showLoading({ title: '加载中...', mask: true });
    
    wx.request({
      url: app.globalData.baseUrl + options.url,
      method: options.method || 'GET',
      data: options.data,
      header: {
        'Content-Type': 'application/json',
        'Authorization': token ? ('Bearer ' + token) : ''
      },
      success: function(res) {
        wx.hideLoading();
        
        console.log('API请求:', options.url, '状态:', res.statusCode);
        
        if (res.statusCode === 401) {
          wx.removeStorageSync('token');
          wx.showToast({
            title: '登录已过期',
            icon: 'none'
          });
          setTimeout(function() {
            wx.navigateTo({ url: '/pages/login/index' });
          }, 1500);
          reject(new Error('登录已过期，请重新登录'));
          return;
        }
        
        if (res.statusCode >= 200 && res.statusCode < 300) {
          if (res.data.success) {
            resolve(res.data);
          } else {
            wx.showToast({ 
              title: res.data.message || '请求失败', 
              icon: 'none' 
            });
            reject(new Error(res.data.message));
          }
        } else {
          wx.showToast({ title: '网络错误', icon: 'none' });
          reject(new Error('网络错误'));
        }
      },
      fail: function(err) {
        wx.hideLoading();
        console.error('请求失败:', err);
        wx.showToast({ title: '网络连接失败', icon: 'none' });
        reject(err);
      }
    });
  });
};

module.exports = { request: request };
