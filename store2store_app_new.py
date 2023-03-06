#!/usr/bin/env python
# coding: utf-8

# *1. reading the utils file (has libraries and custom functions)*

# In[2]:


from utils_new import *


# In[1]:


st.markdown("<h1 style='text-align: center; color: black;'>Store to Store Transfer Engine</h1> \n <h4 style='text-align: center; color: black;font-style: italic;'>To begin please select Brand and Country on the sidebar</h4>", unsafe_allow_html=True)
# st.markdown("<h4 style='text-align: center; color: black;font-style: italic;'>To begin please select Brand and Country on the sidebar</h4>", unsafe_allow_html=True)


# In[ ]:


country_to_use = st.sidebar.selectbox('Select Country',['UAE','KSA','EGY','BAH','KWT'])
country_to_use  = [country_to_use ]
brand_to_use = st.sidebar.selectbox('Select Brand',['Lacoste','Swarovski','Guess'])


# In[ ]:


if brand_to_use == 'Lacoste':
    st.image("https://logos-download.com/wp-content/uploads/2016/02/Lacoste_logo_horizontal.png")
elif brand_to_use == 'Swarovski':
    st.image("https://en.vogue.me/wp-content/uploads/2014/06/SWA_wordmark_rgb_black.png")
elif brand_to_use == 'Guess':
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/89/Guess_logo.svg/2560px-Guess_logo.svg.png")


# In[ ]:


with st.sidebar.form(key='my_form_to_submit'):
    submit_button = st.form_submit_button(label='Submit')


# In[ ]:


if submit_button:
    with st.spinner('Wait for it...'):
        # *2. User Inputs (google sheet to fetch inputs)*
        link_to_gglsht = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vRJDmYDgIAzBkvzuwmbqfw31zltzF4c2XlQ47PP-CUJIBFuLkTMNlAUduacNLnp3H-jTSlIiKX2ePt3/pub?output=xlsx'
        try:
            cover_mdq = read_from_googlesheet( link_to_gglsht , sheet_name='cover_and_mdq')
            cntry_wise_store_vpn_used = read_from_googlesheet( link_to_gglsht , sheet_name='cntry_wise_store_vpn_to_be_used')
            store_grading_lacoste = read_from_googlesheet( link_to_gglsht , sheet_name='store_grading_lacoste')
        
            print(f' shape of cover_mdq : {cover_mdq.shape} \n  shape of cntry_wise_store_vpn_used : {cntry_wise_store_vpn_used.shape} \n shape of store_grading_lacoste : {store_grading_lacoste.shape}')
        except Exception:
            traceback.print_exc()
            print("Exception thrown.")
         
        '''1. User inputs for Cover, VPN, Store, Grading loaded'''
        
        # *3. load data and filtering it for user inputs,rename cols and create sales_status cols*
        link_to_gglsht1 = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vT1YDqLV3OqdRVsVL2ka3K60_RgMdTFoP86_YISo0hpSCAFK-mLbL8FlobpaiYpbHOOFFlgMztJeuHE/pub?output=xlsx'
        try:
            main_df = read_from_googlesheet( link_to_gglsht1 , sheet_name='s2s.csv')

            print(f' shape of main_df_org : {main_df_org.shape}')
        except Exception:
            traceback.print_exc()
            print("Exception thrown.")
        
        # print(f'shape of main_df : {main_df.shape}')
        '''2. Data from googlesheet loaded'''
        print(f'User has selected {country_to_use} to run Store to Store')
        
        main_df['qty_sales']= np.where((main_df['dm_soh_sales.season_desc']== 'BASIC') | (main_df['dm_soh_sales.season_desc']== 'REGULAR') , main_df.total_quantity_sold_6_months , main_df.total_quantity_sold_45_days)
        main_df['net_sales_usd']= np.where((main_df['dm_soh_sales.season_desc']== 'BASIC') | (main_df['dm_soh_sales.season_desc']== 'REGULAR') , main_df.net_sales_amount_usd_6_months , main_df.net_sales_amount_usd_45_days)
        
        main_df.drop(['net_sales_amount_usd_6_months', 'net_sales_amount_usd_45_days','total_quantity_sold_6_months', 'total_quantity_sold_45_days'], axis=1, inplace=True)
        main_df.shape
        
        cols = ['country','store_name','vpn_desc','vpn','prod_id','size','season','taxonomy_class','soh','in_transit_qty' ,'qty_sales','net_sales_usd']
        main_df.columns = cols
        
        ## converting all negative values in qty_sales and net_sales_usd to 0
        main_df['qty_sales'] = np.where(main_df['qty_sales'] < 0, 0, main_df['qty_sales'])
        main_df['net_sales_usd'] = np.where(main_df['net_sales_usd'] < 0, 0, main_df['net_sales_usd'])
        main_df['soh'] = np.where(main_df['soh'] < 0, 0,main_df['soh'])
        main_df.head(2)
        
        
        # for c in ['KSA']:
        '''3. Store to Store for selected Country and Brand begins'''
        for c in country_to_use:
            cntry_wise_store_vpn_used = cntry_wise_store_vpn_used [ cntry_wise_store_vpn_used.country == c ].reset_index(drop=True)
            country_warehouse_name = cntry_wise_store_vpn_used [ cntry_wise_store_vpn_used.store_type == 'warehouse' ].store.values[0]
            print(f'warehouse name in {c} : ',country_warehouse_name)
            df = main_df[(main_df.country == c) &
                        main_df.store_name.isin(list(cntry_wise_store_vpn_used[cntry_wise_store_vpn_used.country == c]['store'].dropna())) &
                        main_df.vpn.isin(list(cntry_wise_store_vpn_used[cntry_wise_store_vpn_used.country == c]['vpn'].dropna()))
                        ].reset_index(drop=True)
            print(c, ':', df.shape)
            
            # '''getting location grade by joining df with cover_mdq file'''
            df = df.merge(store_grading_lacoste[store_grading_lacoste.country==c].reset_index(drop=True), left_on='store_name',right_on='Store Name Actual', how='left')
            df.drop('Store Name Actual', axis=1, inplace=True)
            
            # '''Grade Seasonal and Basic Products separately and then concat both dfs'''
            basic_prod_gd = grade(df[df.season == 'BASIC'], store_col = 'store_name', group_on='prod_id', measure='net_sales_usd', ratio=[60,30,10], grade_labels = ["A","B","C"] )
            seas_prod_gd = grade(df[df.season != 'BASIC'], store_col = 'store_name', group_on='prod_id', measure='net_sales_usd', ratio=[60,30,10], grade_labels = ["nA","nB","nC"])
            prod_gd = pd.concat([basic_prod_gd,seas_prod_gd],axis=0).reset_index(drop=True)
            df = df.merge(prod_gd, left_on=['store_name','prod_id'], right_on = ['store_name','prod_id'] ,how='left',suffixes=('', '___y'))
            df.drop(df.filter(regex='_y$').columns, axis=1, inplace=True)
            
            # '''MDQ and target cover to be joined based on location grade and product grade'''
            ct_cvr_mdq = cover_mdq[cover_mdq.country == c]
            df = df.merge(ct_cvr_mdq, left_on = df['country_x']+'_'+ df['Store Grading'] + '_' + df['prod_id_grade'] ,
                            right_on = ct_cvr_mdq['country']+'_'+ ct_cvr_mdq['Store grade'] + '_' + ct_cvr_mdq['Product grade'] ,
                            how = 'left')
            df = df.drop(['key_0','Store grade','Product grade'],axis=1)
            
            df['avg_monthly_sales_qty'] = np.where(df.season == 'BASIC', round(df.qty_sales/6,2) , round(df.qty_sales/1.5,2))
            df['sell_thru'] = round(df.qty_sales/(df.qty_sales + df.soh),2)
            df['ideal_soh_incl_mdq'] = np.maximum(np.ceil(df.avg_monthly_sales_qty * df.Target_cover) , df.MDQ)
            df['stock_cover'] = round(( df.soh/df.avg_monthly_sales_qty),2)
            df['stock_cover'] = np.where(df['stock_cover'].isna() == True, 0, df['stock_cover'])
        
            # ''' imputing all the values in stock_cover == np.inf (because of 0 avg sales) with the corresponding Target cover'''
            df['stock_cover'] = np.where(df.stock_cover == np.inf, df.Target_cover , df.stock_cover)
            # df['stock_cover_donor'] = [np.inf if df.avg_monthly_sales_qty_donor[i] == 0 else round((df.soh_donor[i]/df.avg_monthly_sales_qty_donor[i]),2) for i in range(0,len(df)) ]
            df['stock_status'] = np.where((df.store_name == country_warehouse_name) & (df.soh > 0) , 'donor' , 'neutral') #look this
            df['stock_status'] = np.where( df.ideal_soh_incl_mdq > (df.soh + df.in_transit_qty) , 'recepient', 'donor')
            df['stock_status'] = np.where( (df.ideal_soh_incl_mdq) == (df.soh + df.in_transit_qty) , 'neutral',df['stock_status'] )

            df['donate_qty'] = np.where( (df.soh > df.ideal_soh_incl_mdq) , df.soh - (df.ideal_soh_incl_mdq) , 0)
            df['required_qty'] = np.where( df.ideal_soh_incl_mdq > (df.soh + df.in_transit_qty) , df.ideal_soh_incl_mdq  - (df.soh + df.in_transit_qty) , 0)

            df['stock_status'] = np.where((df['donate_qty'] == 0) & (df['required_qty'] == 0) , 'neutral', df['stock_status'])
            
            '''4. Transfer logic begins'''
            s2s_output = pd.DataFrame()
            total_uniq_prod_ids = []
            prod_id_valid_for_s2s = []
            rqd_qty_basis_dist_cnt = []
            sales_dist_basis_cnt = []
        
            req_cols = ['country','store_name','Store Grading','prod_id','stock_status','prod_id_grade','vpn_desc','taxonomy_class','vpn','size','season','soh','in_transit_qty','qty_sales','avg_monthly_sales_qty','net_sales_usd','MDQ','Target_cover','sell_thru',
             'ideal_soh_incl_mdq','donate_qty', 'required_qty']
        
            # req_cols = ['store_name','Store Grading','vpn','prod_id','prod_id_grade','stock_status','avg_monthly_sales_qty','MDQ','soh','ideal_soh_incl_mdq','sell_thru', 'donate_qty', 'required_qty']
            # for i in ['018825685992','018825680433']:
            for i in df.prod_id.unique():
                total_uniq_prod_ids.append(i)
        
                sub = df[df.prod_id == i][req_cols]
                sub['store_city'] = [i.split('- ')[-1] for i in sub['store_name']]
                sub=sub[req_cols[0:1] + ['store_city'] + req_cols[1:]]
        
                if (('recepient' not in sub.stock_status.unique()) or ('donor' not in sub.stock_status.unique())) == False: 
                    prod_id_valid_for_s2s.append(i)
                    donor_sub = sub[sub['stock_status']=='donor'].drop('required_qty',axis=1).sort_values(by=['avg_monthly_sales_qty','sell_thru','Store Grading'],
                                                                                                          ascending = [True,True,False]).reset_index(drop=True)
                    donor_sub = pd.concat([donor_sub[donor_sub["store_name"] == country_warehouse_name], donor_sub[donor_sub["store_name"] != country_warehouse_name]])
                    donor_sub = donor_sub.reset_index(drop=True)
                    donor_sub['donate_qty_cusum'] = donor_sub.donate_qty.cumsum()
                    
                    recepient_sub = sub[sub['stock_status']=='recepient'].drop('donate_qty',axis=1).sort_values(by=['avg_monthly_sales_qty','sell_thru','Store Grading'],
                                                                                                                ascending = [False,False,True]).reset_index(drop=True)
                    donor_sub['original_can_donate_qty'] = donor_sub.donate_qty
        
                    for j in recepient_sub.store_name.unique():  ## adding column with store_names to input received units from each store
                        donor_sub.insert(loc = donor_sub.shape[1],column= j, value='')
        
                    # try
                    fulfil_all = (sum(donor_sub.donate_qty)/sum(recepient_sub.required_qty) ) >= 1
                    ## allocation algo
                    if fulfil_all == True:
                        rqd_qty_basis_dist_cnt.append(i)
                        # --DISTRIBUTION BASIS REQUIRED QTY--
                        donor_sub = allocation_algo(donor_sub, recepient_sub, donor_qty_col = 'donate_qty', recep_qty_col = 'required_qty' , store_name_col = 'store_name')
                        donor_sub.insert(loc = donor_sub.shape[1] - len(recepient_sub.store_name.unique()) ,column = 'algo_used',value = 'Greedy')
                        donor_sub = data_prep_v1(donor_sub, recepient_sub)
                        donor_sub['key'] = donor_sub['recipient_store_name'] + '_' + donor_sub['prod_id']
                        recepient_sub['key'] = recepient_sub['store_name'] + '_' + recepient_sub['prod_id']
                        donor_sub = donor_sub.merge(recepient_sub.drop('country',axis=1) , on = 'key' , how='left' , suffixes = ('_donor','_recipient'))
                    else:
                        sales_dist_basis_cnt.append(i)
                        # --DISTRIBUTION BASIS SALES CONTRIBUTION--
                        recepient_sub['avg_sales_prop'] = recepient_sub.avg_monthly_sales_qty/sum(recepient_sub.avg_monthly_sales_qty)
                        recepient_sub['proportionate_rqd_qty'] = np.ceil(recepient_sub['avg_sales_prop'] * sum(donor_sub.donate_qty))
                        donor_sub = allocation_algo(donor_sub, recepient_sub, donor_qty_col = 'donate_qty', recep_qty_col = 'proportionate_rqd_qty' , store_name_col = 'store_name')
                        donor_sub.insert(loc = donor_sub.shape[1] - len(recepient_sub.store_name.unique()) ,column = 'algo_used',value = 'Proportionate')
                        donor_sub = data_prep_v1(donor_sub, recepient_sub)
                        donor_sub['key'] = donor_sub['recipient_store_name'] + '_' + donor_sub['prod_id']
                        recepient_sub['key'] = recepient_sub['store_name'] + '_' + recepient_sub['prod_id']
                        donor_sub = donor_sub.merge(recepient_sub.drop('country',axis=1) , on = 'key' , how='left' , suffixes = ('_donor','_recipient'))
        
                    s2s_output = s2s_output.append(donor_sub, ignore_index=True)  
        
            print(f'        Total unique prod_ids : {len(total_uniq_prod_ids)}\n                    % of prod_id valid for s2s : {round(100*len(prod_id_valid_for_s2s)/len(total_uniq_prod_ids),2)}% \n                    % of prod_ids that went through Greedy algo : {round(100*len(rqd_qty_basis_dist_cnt)/len(total_uniq_prod_ids),2)}% \n                    % of prod_ids that went through sales contr based allocation algo : {round(100*len(sales_dist_basis_cnt)/len(total_uniq_prod_ids),2)}%')
            
            '''5. Final data prep begins'''
            # ''' logic to get donated_qty for each donor in s2s_output'''
            temp = s2s_output[['store_name_donor', 'prod_id_donor','original_can_donate_qty','qty_received']].groupby(['store_name_donor', 'prod_id_donor','original_can_donate_qty']).sum().reset_index()
            temp.columns = ['store_name_donor', 'prod_id_donor','original_can_donate_qty','donated_qty']
            temp['key2'] = temp.store_name_donor + temp.prod_id_donor
        
            s2s_output['key2'] = s2s_output.store_name_donor + s2s_output.prod_id_donor
            s2s_output = s2s_output.merge(temp[['key2','donated_qty']] , on='key2', how='left')
            
            
            # '''calculating a few metrics'''
            s2s_output['qty_remaining_after_alloc'] = s2s_output.soh_donor - s2s_output.donated_qty
            s2s_output['new_soh_donor'] = s2s_output.soh_donor -  s2s_output.donated_qty
            s2s_output['new_soh_recipient'] = s2s_output.soh_recipient + s2s_output.qty_received
        
            s2s_output['stock_cover_donor'] = [np.inf if s2s_output.avg_monthly_sales_qty_donor[i] == 0 else round((s2s_output.soh_donor[i]/s2s_output.avg_monthly_sales_qty_donor[i]),2) for i in range(0,len(s2s_output)) ]
            s2s_output['stock_cover_recipient'] = [np.inf if s2s_output.avg_monthly_sales_qty_recipient[i] == 0 else round((s2s_output.soh_recipient[i]/s2s_output.avg_monthly_sales_qty_recipient[i]),2) for i in range(0,len(s2s_output)) ]
        
            s2s_output['new_stock_cover_donor'] = [np.inf if s2s_output.avg_monthly_sales_qty_donor[i] == 0 else round((s2s_output.new_soh_donor[i]/s2s_output.avg_monthly_sales_qty_donor[i]),2) for i in range(0,len(s2s_output)) ]
            s2s_output['new_stock_cover_recipient'] = [np.inf if s2s_output.avg_monthly_sales_qty_recipient[i] == 0 else round((s2s_output.new_soh_recipient[i]/s2s_output.avg_monthly_sales_qty_recipient[i]),2) for i in range(0,len(s2s_output)) ]
            
            cols_2 = ['country', 'store_city_donor', 'store_name_donor','Store Grading_donor', 'prod_id_donor', 'stock_status_donor','prod_id_grade_donor', 'vpn_desc_donor', 'taxonomy_class_donor','vpn_donor', 'size_donor', 'season_donor', 'soh_donor','new_soh_donor','stock_cover_donor','new_stock_cover_donor',
               'in_transit_qty_donor', 'qty_sales_donor','avg_monthly_sales_qty_donor', 'net_sales_usd_donor', 'MDQ_donor','Target_cover_donor', 'sell_thru_donor', 'ideal_soh_incl_mdq_donor','original_can_donate_qty', 'donated_qty','qty_remaining_after_alloc',
                'algo_used', 'recipient_store_name','qty_received', 'store_city_recipient','Store Grading_recipient', 'prod_id_recipient','stock_status_recipient', 'soh_recipient','new_soh_recipient','stock_cover_recipient','new_stock_cover_recipient','in_transit_qty_recipient', 'qty_sales_recipient',
                'avg_monthly_sales_qty_recipient', 'net_sales_usd_recipient','MDQ_recipient', 'Target_cover_recipient','sell_thru_recipient','ideal_soh_incl_mdq_recipient', 'required_qty', 'avg_sales_prop','proportionate_rqd_qty' ]
            
            s2s_output.qty_received = np.where((s2s_output.algo_used == 'Proportionate')&(s2s_output.qty_received == 0) , 'Not received' , s2s_output.qty_received)
            s2s_output_whole = s2s_output[cols_2]
            s2s_output_focus = s2s_output[['country','store_name_donor','prod_id_donor','vpn_donor','stock_status_donor','original_can_donate_qty','donated_qty','qty_remaining_after_alloc','recipient_store_name', 'required_qty','qty_received','stock_cover_recipient','new_stock_cover_recipient']]
             
            '''6. Output Data Prep Done'''
            
            ## Stock cover change analysis
            # donor_sc_op = s2s_output[['store_name_donor','Store Grading_donor','prod_id_donor', 'prod_id_grade_donor','stock_cover_donor','new_stock_cover_donor']].drop_duplicates().sort_values('prod_id_donor').reset_index(drop=True)
            # donor_sc_op = donor_sc_op.groupby(['Store Grading_donor','prod_id_grade_donor'])['stock_cover_donor','new_stock_cover_donor'].apply(lambda x: (x >= 1).sum()).reset_index()
            # donor_sc_op.columns = ['Store Grading_donor', 'prod_id_grade_donor', 'before_alloc_greater_than_1_SC_count_donor','after_alloc_greater_than_1_SC_count_donor']
            # donor_sc_op['donor_sc_pct_change'] = round((100*(donor_sc_op.after_alloc_greater_than_1_SC_count_donor - donor_sc_op.before_alloc_greater_than_1_SC_count_donor))/donor_sc_op.before_alloc_greater_than_1_SC_count_donor,0)
            # # donor_sc_op.to_csv(metric_path + '\\' + 'donor_sc_analysis.csv')
            
            # recep_sc_op = s2s_output[['store_name_recipient','Store Grading_recipient','prod_id_recipient', 'prod_id_grade_recipient','stock_cover_recipient','new_stock_cover_recipient']]
            # recep_sc_op = recep_sc_op.groupby(['Store Grading_recipient','prod_id_grade_recipient'])['stock_cover_recipient','new_stock_cover_recipient'].apply(lambda x: (x >= 1).sum()).reset_index()
            # recep_sc_op.columns = ['Store Grading_recipient','prod_id_grade_recipient', 'before_alloc_greater_than_1_SC_count_recep','after_alloc_greater_than_1_SC_count_recep']
            # recep_sc_op['recep_sc_pct_change'] = round((100*(recep_sc_op.after_alloc_greater_than_1_SC_count_recep - recep_sc_op.before_alloc_greater_than_1_SC_count_recep))/recep_sc_op.before_alloc_greater_than_1_SC_count_recep,0)
            # # recep_sc_op.to_csv(metric_path + '\\' + 'recipient_sc_analysis.csv')
            
            # ## SOH change analysis
            # donor_soh_op = s2s_output[['store_name_donor','Store Grading_donor','prod_id_donor', 'prod_id_grade_donor','soh_donor','new_soh_donor']].drop_duplicates().sort_values('prod_id_donor').reset_index(drop=True)
            # donor_soh_op = donor_soh_op.groupby(['Store Grading_donor','prod_id_grade_donor'])['soh_donor','new_soh_donor'].sum().reset_index()
            # donor_soh_op.columns = ['Store Grading_donor', 'prod_id_grade_donor', 'before_alloc_SOH','after_alloc_SOH']
            # donor_soh_op['donor_soh_pct_change'] = round((100*(donor_soh_op.after_alloc_SOH - donor_soh_op.before_alloc_SOH))/donor_soh_op.after_alloc_SOH,0)
            # # donor_soh_op.to_csv(metric_path + '\\' + 'donor_SOH_analysis.csv')
            
            # recep_soh_op = s2s_output[['store_name_recipient','Store Grading_recipient','prod_id_recipient', 'prod_id_grade_recipient','soh_recipient','new_soh_recipient']]
            # recep_soh_op = recep_soh_op.groupby(['Store Grading_recipient','prod_id_grade_recipient'])['soh_recipient','new_soh_recipient'].sum().reset_index()
            # recep_soh_op.columns = ['Store Grading_recipient','prod_id_grade_recipient', 'before_alloc_SOH','after_alloc_SOH']
            # recep_soh_op['recep_soh_pct_change'] = round((100*(recep_soh_op.after_alloc_SOH - recep_soh_op.before_alloc_SOH))/recep_soh_op.after_alloc_SOH,0)
            # recep_soh_op.to_csv(metric_path + '\\' + 'recipient_SOH_analysis.csv')
        
            st.success('Hurray ðŸŽ‰ðŸŽ‰ Allocation Done! ðŸŽ‰ðŸŽ‰, You can Download the output . In case of any issues and suggestions please reach out to manish.bansal@chalhoub.com')
            st.balloons()
            st.snow()
            df_xlsx = to_excel(df_sheet = {'focus':s2s_output_focus, 'whole':s2s_output_whole 
                                           # ,'Donor_stock_cover_analysis':donor_sc_op,
                                           # 'Recep_stock_cover_analysis':recep_sc_op,
                                           # 'Donor_SOH_analysis':donor_soh_op,
                                           # 'Recep_SOH_analysis':recep_soh_op
                                           })
            
            st.download_button(label='ðŸ“¥ Download Store to Store Output',
                                            data=df_xlsx ,
                                            file_name= c+'_store2store_output.xlsx')
            
            st.dataframe(s2s_output_focus)
    

