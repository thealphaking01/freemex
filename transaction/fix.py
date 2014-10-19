from django.shortcuts import render_to_response
from login.models import login,user_share,notification
from stock.models import share
from django.template import RequestContext
from django.http import HttpResponse,HttpResponseRedirect
from transaction.models import bid,offer,transactions


from django.db.models import Q


def fix(request):
	logins = login.objects.all()
	dummy = login.objects.get(email='dummy@dummy.com')
	for userLogin in logins:
		if userLogin == dummy:
			continue
		
		trans = transactions.objects.filter(Q(buyer=userLogin) | Q(seller=userLogin))
		money = 100000
		shares = {}
		for t in trans:
			if t.buyer == userLogin:
				transactionTotal = t.quantity * t.price
				if money < transactionTotal:
					t.buyer = dummy
					t.save()
					continue
				money = money - transactionTotal
				if t.share in shares.keys():
					shares[t.share] += t.quantity
				else:
					shares[t.share] = t.quantity
			elif t.seller == userLogin:
				transactionTotal = t.quantity * t.price
				if t.share in shares.keys():
					if shares[t.share] < t.quantity:
						t.seller = dummy
						t.save()
						continue						
					money = money + transactionTotal
					shares[t.share] -= t.quantity
				else:
					t.seller = dummy
					t.save()
					continue
					
		userLogin.money = money
		userLogin.save()
		try:
			userShares = user_share.objects.filter(user=userLogin)
			for i in userShares:
				i.delete()
		except:
			pass
		for i in shares.keys():
			us = user_share(user=userLogin, share=i, quantity=shares[i])
			us.save()
	return HttpResponse('done.')
