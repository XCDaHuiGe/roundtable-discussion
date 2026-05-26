
(function(){
var deck=document.getElementById("deck");
var slides=deck.querySelectorAll(".slide");
var total=slides.length;
var cur=0;
var dots=document.getElementById("navDots");
var tocList=document.getElementById("tocList");
var titleEl=document.getElementById("slideTitle");
var counterEl=document.getElementById("slideCounter");
var tocPanel=document.getElementById("tocPanel");
var tocBackdrop=document.getElementById("tocBackdrop");
var progressBar=document.getElementById("progressBar");

for(var i=0;i<total;i++){
  var d=document.createElement("button");
  d.className="nd";
  d.setAttribute("data-i",i);
  d.onclick=(function(idx){return function(){go(idx)}})(i);
  dots.appendChild(d);
  var t=document.createElement("div");
  t.className="toc-item";
  t.setAttribute("data-i",i);
  t.innerHTML='<span class="toc-label">'+(slides[i].getAttribute("data-title")||"Slide "+(i+1))+'</span><span class="toc-page">'+String(i+1).padStart(2,"0")+'</span>';
  t.onclick=(function(idx){return function(){go(idx);closeTOC()}})(i);
  tocList.appendChild(t);
}

function go(n){
  if(n<0||n>=total)return;
  slides[cur].classList.remove("active");
  dots.children[cur].classList.remove("active");
  tocList.children[cur].classList.remove("active");
  cur=n;
  slides[cur].classList.add("active");
  dots.children[cur].classList.add("active");
  tocList.children[cur].classList.add("active");
  titleEl.textContent=slides[cur].getAttribute("data-title")||"";
  counterEl.textContent=(cur+1)+" / "+total;
  progressBar.style.width=((cur+1)/total*100)+"%";
  slides[cur].scrollTop=0;
}
function toggleTOC(){tocPanel.classList.toggle("open");tocBackdrop.classList.toggle("open")}
function closeTOC(){tocPanel.classList.remove("open");tocBackdrop.classList.remove("open")}

document.addEventListener("keydown",function(e){
  if(e.key==="ArrowRight"||e.key==="ArrowDown"||e.key===" "||e.key==="PageDown"){e.preventDefault();go(cur+1)}
  else if(e.key==="ArrowLeft"||e.key==="ArrowUp"||e.key==="PageUp"){e.preventDefault();go(cur-1)}
  else if(e.key==="Home"){e.preventDefault();go(0)}
  else if(e.key==="End"){e.preventDefault();go(total-1)}
  else if(e.key==="Escape"){closeTOC();go(0)}
  else if(e.key==="t"||e.key==="T"){toggleTOC()}
});
var wheelTimer=null;
deck.addEventListener("wheel",function(e){e.preventDefault();if(wheelTimer)return;wheelTimer=setTimeout(function(){wheelTimer=null},350);if(e.deltaY>0)go(cur+1);else if(e.deltaY<0)go(cur-1)},{passive:false});
var touchX=0,touchY=0;
deck.addEventListener("touchstart",function(e){touchX=e.touches[0].clientX;touchY=e.touches[0].clientY});
deck.addEventListener("touchend",function(e){
  var dx=touchX-e.changedTouches[0].clientX,dy=touchY-e.changedTouches[0].clientY;
  if(Math.abs(dy)>Math.abs(dx)){if(dy>50)go(cur+1);else if(dy<-50)go(cur-1)}
  else{if(dx>50)go(cur+1);else if(dx<-50)go(cur-1)}
});
deck.addEventListener("click",function(e){
  if(e.target.closest(".nav-btn,.nd,.toc-item,.toc-panel,.toc-backdrop"))return;
  go(cur+1);
});
document.getElementById("btnToc").addEventListener("click",function(e){e.stopPropagation();toggleTOC()});
document.getElementById("btnPrev").addEventListener("click",function(e){e.stopPropagation();go(cur-1)});
document.getElementById("btnNext").addEventListener("click",function(e){e.stopPropagation();go(cur+1)});
tocBackdrop.addEventListener("click",closeTOC);
go(0);
})();
