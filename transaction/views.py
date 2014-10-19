from django.shortcuts import render_to_response
from login.models import login,user_share,notification
from stock.models import share
from freemex import settings
from django.template import RequestContext
from django.http import HttpResponse,HttpResponseRedirect
from transaction.models import bid,offer,transactions
from login.views import buyShareList,BidForm
import random,decimal,math
from django.db.models import Q
from datetime import datetime
import json

def randrange_float(start, stop, step):
	rand = random.randint(0, round((stop - start) / step)) * step + start
	rand = round(20*rand)/20
	return rand
	
def dummy(shareId,request):
	dummy = login.objects.get(email='dummy@dummy.com')
	#change dummy money here
	try:
		bidMoney = bid.objects.filter(bidder_id=request.session['login_id'],share=shareId).order_by('-id')[0].quote
		bidQuantity = bid.objects.filter(bidder_id=request.session['login_id'],share=shareId).order_by('-id')[0].quantity
		totalBidValue = bidMoney*bidQuantity
	except:
		totalBidValue = 0
	try:
		offerMoney = offer.objects.filter(seller_id=request.session['login_id'],share=shareId).order_by('-id')[0].quote
		offerQuantity = offer.objects.filter(seller_id=request.session['login_id'],share=shareId).order_by('-id')[0].quantity
		totalOfferValue = offerMoney*offerQuantity
	except:
		totalOfferValue = 0
	try:
		current_price = ((transactions.objects.filter(share=shareId).order_by('-id'))[0]).price
	except:
		current_price = shareId.day_value
	totalValue=max(totalBidValue, totalOfferValue)
	
	dummyquantity = totalValue * 0.4 / current_price
	if dummyquantity<1:
		dummyquantity = 10
	multiplier = 0.01
	if shareId.id == 13:
		multiplier = 0.03
	start = current_price
	stopbid = current_price  - shareId.day_value * multiplier
	stopoffer = current_price + shareId.day_value * multiplier
	step = 0.001
	f = .001
	
	for i in range(3):
		b = bid(bidder=dummy, share=shareId, quantity=dummyquantity, quote=round((random.randrange(round(stopbid/f),round(start/f),round(step/f))*f),2))
		s = offer(seller=dummy, share=shareId, quantity=dummyquantity, quote=round((random.randrange(round(start/f),round(stopoffer/f),round(step/f))*f),2))
		b.save()
		s.save()
	
	checktransaction(shareId, "bid", request)
	
def deletebid(request):
	date = datetime.now()
	hour = (date.time()).hour
	if hour > 0:
		message = notification(user_id=request.session['login_id'],notification = "Order cannot be processed. Market Closed")
		message.save()
		return HttpResponse(json.dumps({"server_response":"wronginput"}), mimetype='application/javascript')
		return HttpResponseRedirect('/portfolio/')
	if request.method == 'POST':
		b = bid.objects.get(pk=request.POST['transaction_id'])
		b.delete()
		return HttpResponseRedirect(request.META['HTTP_REFERER'])
	else:
		return HttpResponseRedirect(request.META['HTTP_REFERER'])

def deleteoffer(request):
	date = datetime.now()
	hour = (date.time()).hour
	if hour > 0:
		message = notification(user_id=request.session['login_id'],notification = "Order cannot be processed. Market Closed")
		message.save()
		return HttpResponse(json.dumps({"server_response":"wronginput"}), mimetype='application/javascript')
		return HttpResponseRedirect('/portfolio/')
	if request.method == 'POST':
		s = offer.objects.get(pk=request.POST['transaction_id'])
		s.delete()
		return HttpResponseRedirect(request.META['HTTP_REFERER'])
	else:
		return HttpResponseRedirect(request.META['HTTP_REFERER'])
		
def bidmodify(request):
	date = datetime.now()
	hour = (date.time()).hour
	if hour > 0:
		message = notification(user_id=request.session['login_id'],notification = "Order cannot be processed. Market Closed")
		message.save()
		return HttpResponse(json.dumps({"server_response":"wronginput"}), mimetype='application/javascript')
		return HttpResponseRedirect('/marketwatch/')
	if request.method == 'POST':
		if request.POST['quantity']=="" or request.POST['quote']=="":
			return HttpResponse(json.dumps({"server_response":"wronginput"}), mimetype='application/javascript')
		try:
			b = bid.objects.get(pk=request.POST['transaction_id'])
		except:
			return HttpResponseRedirect('/portfolio/')
		b.quantity=request.POST['quantity']
		b.quote = request.POST['quote']
		shareId = b.share
		min = round(shareId.day_value * 0.9, 2) 
		max = round(shareId.day_value * 1.1, 2)
		quote = round(decimal.Decimal(b.quote), 2)
		if quote < min or quote > max:
			message = notification(user_id=request.session['login_id'],notification="Quote unsuccessful. Quote price out of bounds")
			message.save()
	                return HttpResponse(json.dumps({"server_response":"wronginput"}), mimetype='application/javascript')

		b.save()
		
		data = "bid"
		dummy(shareId,request)
		checktransaction(shareId,data,request)
                return HttpResponse(json.dumps({"server_response":"biddone"}), mimetype='application/javascript')

	else:
		return HttpResponseRedirect(request.META['HTTP_REFERER'])

def offermodify(request):
	date = datetime.now()
	hour = (date.time()).hour
	if hour > 0:
		message = notification(user_id=request.session['login_id'],notification = "Order cannot be processed. Market Closed")
		message.save()
		return HttpResponse(json.dumps({"server_response":"wronginput"}), mimetype='application/javascript')
		return HttpResponseRedirect('/marketwatch/')
	if request.method == 'POST':
		if request.POST['quantity']=="" or request.POST['quote']=="":
                	return HttpResponse(json.dumps({"server_response":"wronginput"}), mimetype='application/javascript')
		try:
			o = offer.objects.get(pk=request.POST['transaction_id'])
		except:
			return HttpResponseRedirect('/portfolio/')
		shareId = o.share
		o.quantity=request.POST['quantity']
		o.quote = request.POST['quote']

		userShare = user_share.objects.get(user_id=request.session['login_id'],share=shareId)
		min = round(shareId.day_value * 0.9, 2) 
		max = round(shareId.day_value * 1.1, 2)
		quote = round(decimal.Decimal(o.quote), 2)
		if quote < min or quote > max:
			message = notification(user_id=request.session['login_id'],notification="Quote unsuccessful. Quote price out of bounds")
			message.save()
	                return HttpResponse(json.dumps({"server_response":"wronginput"}), mimetype='application/javascript')

		if int(o.quantity) > userShare.quantity:
			message = notification(user_id=request.session['login_id'],notification="Quote unsuccessful. Not enough stocks to sell")
			message.save()
                	return HttpResponse(json.dumps({"server_response":"wronginput"}), mimetype='application/javascript')

		
		o.save()
		data = "sell"
		dummy(shareId,request)
		checktransaction(shareId,data,request)
                return HttpResponse(json.dumps({"server_response":"offerdone"}), mimetype='application/javascript')
	else:
		return HttpResponseRedirect(request.META['HTTP_REFERER'])

def bidcheck(request):
	date = datetime.now()
	hour = (date.time()).hour
	if hour > 0:
		message = notification(user_id=request.session['login_id'],notification = "Order cannot be processed. Market Closed")
		return HttpResponse(json.dumps({"server_response":"wronginput"}), mimetype='application/javascript')
		message.save()
		return HttpResponseRedirect('/marketwatch/')
# remember to change response type
	if request.method == 'POST':
	        if request.POST['quantity']=="" or request.POST['price']=="":
        	        return HttpResponse(json.dumps({"server_response":"wronginput"}), mimetype='application/javascript')
		shareId = share.objects.get(pk=request.POST['share'])
		bidderId = login.objects.get(pk=request.session['login_id'])
		b = bid(bidder = bidderId, share = shareId, quantity=request.POST['quantity'], quote=request.POST['price'])
		min = round(shareId.day_value * 0.9, 2)
		max = round(shareId.day_value * 1.1, 2)
		quote = round(decimal.Decimal(b.quote), 2)
		if quote < min or quote > max:
			message = notification(user_id=request.session['login_id'],notification = "Quote unsuccessful. Quote price out of bounds")
			message.save()
	                return HttpResponse(json.dumps({"server_response":"wronginput"}), mimetype='application/javascript')

		b.save()
		data = "bid"
		dummy(shareId,request)
		checktransaction(shareId,data,request)
#		return HttpResponseRedirect(request.META['HTTP_REFERER'])
		return HttpResponse(json.dumps({"server_response":"biddone"}), mimetype='application/javascript')
	else:
                return HttpResponseRedirect('/marketwatch/')
     
			
def offercheck(request):
	date = datetime.now()
	hour = (date.time()).hour
       	
	if hour > 0:
		message = notification(user_id=request.session['login_id'],notification = "Order cannot be processed. Market Closed")
		return HttpResponse(json.dumps({"server_response":"wronginput"}), mimetype='application/javascript')
		message.save()
		return HttpResponseRedirect('/marketwatch/')
	if request.method == 'POST':
	        if request.POST['quantity']=="" or request.POST['price']=="":
        	        return HttpResponse(json.dumps({"server_response":"wronginput"}), mimetype='application/javascript')

		shareId = share.objects.get(pk=request.POST['share'])
		sellerId = login.objects.get(pk=request.session['login_id'])
		s = offer(seller = sellerId ,share = shareId , quantity=request.POST['quantity'],quote=request.POST['price'])
		userShare = user_share.objects.get(user_id=request.session['login_id'],share=shareId)
		min = round(shareId.day_value * 0.9, 2) 
		max = round(shareId.day_value * 1.1, 2)
		quote = round(decimal.Decimal(s.quote), 2)
		if quote < min or quote > max:
			message = notification(user_id=request.session['login_id'],notification="Quote unsuccessful. Quote price out of bounds")
			message.save()
	                return HttpResponse(json.dumps({"server_response":"wronginput"}), mimetype='application/javascript')
		if int(s.quantity) > userShare.quantity:
			message = notification(user_id=request.session['login_id'],notification="Quote unsuccessful. Not enough stocks to sell")
			message.save()
	                return HttpResponse(json.dumps({"server_response":"wronginput"}), mimetype='application/javascript')

			
		
		s.save()
		data = "sell"
		dummy(shareId,request)
		checktransaction(shareId,data,request)
		return  HttpResponse(json.dumps({"server_response":"offerdone"}), mimetype='application/javascript')
	else:
		return HttpResponseRedirect(request.META['HTTP_REFERER'])
		
		

def checktransaction(share, data, request):
	bids = bid.objects.filter(share=share).order_by('-quote')
	offers = offer.objects.filter(share=share).order_by('quote')

	shareName = share.name
	dummy = login.objects.get(email='dummy@dummy.com')
	flag = 1
	for o in offers:
		if flag == 0:
			break
		for b in bids:						
			try:
				if (o.quote <= b.quote):
					price = (o.quote + b.quote)/2
					buyer = b.bidder
					seller = o.seller

					if o.quantity < b.quantity:
						quantity = o.quantity
					else:
						quantity = b.quantity

					transactionTotal = quantity * price
					#Check if buyer has enough money
					if buyer.money < (b.quantity * price):
						note = notification(user=buyer, notification="Your bid for " +shareName+ " got deleted due to lack of money")
						note.save()
						b.delete()
						continue
					#Check if seller has enough shares
					if (user_share.objects.filter(user=seller, share=share)):
						ss = user_share.objects.get(user=seller, share=share)
						if (ss.quantity < o.quantity):
							note = notification(user=seller, notification="Your offer for " +shareName+ " got deleted due to lack of share")
							note.save()
							o.delete()
							break
					else:
						note = notification(user=seller, notification="Your offer for " +shareName+ " got deleted due to lack of share")
						note.save()
						o.delete()
						break

					if (buyer!=seller):
						if (user_share.objects.filter(user=buyer, share=share)):
							bs = user_share.objects.get(user=buyer, share=share)														
							bs.quantity = bs.quantity + quantity
						else:
							bs = user_share(user=buyer, share=share, quantity=quantity)
						bs.save()

						if (seller != dummy):
							ss.quantity = ss.quantity - quantity
							ss.save()

						if (buyer != dummy):
							buyer.money = buyer.money - transactionTotal							
							buyer.save()

						seller.money = seller.money + transactionTotal
						seller.save()												

					try:
						t=transactions(buyer=b.bidder, seller=o.seller, share=share, quantity=quantity, price=price)
						t.save()
						noteBuyer = notification(user=buyer, notification=str(quantity)+" shares of "+share.name+" bought at "+str(price))
						noteSeller = notification(user=seller,notification=str(quantity)+" shares of "+share.name+" sold at "+str(price))
						noteBuyer.save()
						noteSeller.save()
					except IndexError:
						break

					if o.quantity < b.quantity:						
						b.quantity = b.quantity - o.quantity
						b.save()
						o.delete()
						break
					else:						
						o.quantity = o.quantity - b.quantity
						if o.quantity == 0:
							o.delete()
							break
						else:
							o.save()
						b.delete()
						continue
				elif (o.quote > b.quote):
					flag = 0
					break

			except IndexError:
				break
