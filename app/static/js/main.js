$(document).ready(function() {

    if (!Modernizr.input.placeholder) {
        var script = document.createElement( 'script' );
        script.type = "text/javascript";
        script.src = '/static/js/libs/jquery.placeholder.js';
        $('body').append(script);
        $('input').placeholder();
    }

    // Share plugin
    $('.share-js').share({
        url: 'http://guildbit.com',
        text: 'Guildbit - Free 15 slot Mumble servers. No registration required!',
        button_text: 'Share Us!'
    });

    // GA link event tracking wrapper
    $(".track").click(function () {
        var label =  $(this).attr("data-event-label");
        ga('send', 'event', 'link', 'click', label);
        window.setTimeout("window.location.href='" + this.href + "'", 100);
        return false;
    });

    // GA link event tracking wrapper
    $(".track-nolink").click(function () {
        var label =  $(this).attr("data-event-label");
        ga('send', 'event', 'link', 'click', label);
    });

    // GA submit event tracking wrapper
    $(".track-submit").click(function (e) {
        e.preventDefault();
        var label =  $(this).attr("data-event-label");
        ga('send', 'event', 'button', 'click', label);
        var form = $(this);
        setTimeout(function() {
            form.closest("form").submit();
        }, 200);
    });

    // Download Mumble OS chooser
    if (os.indexOf("Linux") !== -1 && ua.indexOf("android") === -1) {
        $('#os-download #os-text').text(_LinuxDownload);
        $('#os-download #download-link i').removeClass('fa-windows');
        $('#os-download #download-link i').addClass('fa-linux');
        $('#os-download #download-link').attr('href', 'http://mumble.sourceforge.net/Installing_Mumble#Linux');
        }
    else if (os.indexOf("Win") !== -1) {
        $('#os-download #os-text').text(_WindowsDownload);
        $('#os-download #download-link i').addClass('fa-windows');
        $('#os-download #download-link').attr('href', 'http://sourceforge.net/projects/mumble/files/Mumble/1.2.8/mumble-1.2.8.msi/download');
        }
    else if (os.indexOf("MacOS") !== -1 || os.indexOf("MacIntel") !== -1) {
        $('#os-download #os-text').text(_OSXDownload);
        $('#os-download #download-link i').removeClass('fa-windows');
        $('#os-download #download-link i').addClass('fa-apple');
        $('#os-download #download-link').attr('href', 'http://sourceforge.net/projects/mumble/files/Mumble/1.2.8/Mumble-1.2.8.dmg/download');
        }
    else if (ua.indexOf("android") > -1) {
        $('#os-download #os-text').text(_AndroidDownload);
        $('#os-download #download-link i').removeClass('fa-windows');
        $('#os-download #download-link i').addClass('fa-android');
        $('#os-download #download-link').attr('href', 'https://play.google.com/store/apps/details?id=com.morlunk.mumbleclient');
        }
    else if (os === 'iPad' || os == 'iPhone' || os === 'iPod') {
        $('#os-download #os-text').text(_iOSDownload);
        $('#os-download #download-link i').removeClass('fa-windows');
        $('#os-download #download-link i').addClass('fa-apple');
        $('#os-download #download-link').attr('href', 'https://itunes.apple.com/us/app/mumble/id443472808');
        }

});