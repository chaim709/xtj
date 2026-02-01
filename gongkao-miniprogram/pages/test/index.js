Page({
  data: {
    message: '测试页面',
    count: 0
  },
  
  onLoad: function() {
    console.log('测试页面加载成功');
  },
  
  handleClick: function() {
    this.setData({
      count: this.data.count + 1
    });
    console.log('点击次数:', this.data.count);
  }
});
