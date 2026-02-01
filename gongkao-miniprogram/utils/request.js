const app = getApp();

const request = (options) => {
  return new Promise((resolve, reject) => {
    const token = wx.getStorageSync('token');
    
    wx.showLoading({ title: '加载中...', mask: true });
    
    wx.request({
      url: app.globalData.baseUrl + options.url,
      method: options.method || 'GET',
      data: options.data,
      header: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
      },
      success: (res) => {
        wx.hideLoading();
        
        if (res.statusCode === 401) {
          wx.removeStorageSync('token');
          wx.navigateTo({ url: '/pages/login/index' });
          reject(new Error('登录已过期，请重新登录'));
          return;
        }
        
        if (res.statusCode >= 200 && res.statusCode < 300) {
          if (res.data.success) {
            resolve(res.data);
          } else {
            wx.showToast({ title: res.data.message || '请求失败', icon: 'none' });
            reject(new Error(res.data.message));
          }
        } else {
          wx.showToast({ title: '网络错误', icon: 'none' });
          reject(new Error('网络错误'));
        }
      },
      fail: (err) => {
        wx.hideLoading();
        wx.showToast({ title: '网络连接失败', icon: 'none' });
        reject(err);
      }
    });
  });
};

module.exports = { request };
