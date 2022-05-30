
$('nav a').on('click', function(e) {                 
    e.preventDefault();  // 阻止鏈接跳轉
    var url = this.href;  // 保存點擊的地址

    $('nav a.current').removeClass('current');    
    $(this).addClass('current');                       

    $('#container').remove();                          
    $('#content').load(url + ' #container').fadeIn('slow'); // 載入新內容,url地址與該地址下的選擇器之間要有空格,表示該url下的#container
});