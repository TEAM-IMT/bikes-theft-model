from CreatingData import *
from math import *
import sklearn.metrics as metrics 

def Train(n_epochs,model,training_generator,optimizer_rnn,criterion,validation_generator,scheduler,model_name,fig):
    train_losses, valid_losses = [], []
    # initialize tracker for minimum validation loss
    valid_loss_min = np.Inf  # set initial "min" to infinity

    print("MODEL Adam")
    for epoch in range(1,n_epochs+1):

        ls = 0
        valid_ls=0

        model.train() # prep model for training

        for xb, yb in training_generator: #ix,xb,yb 

            # print(xb.shape)
            # print(yb.shape)
            # Perform the forward pass operation
            Input_tensor = xb.unsqueeze(0)  # (1,32,60) (Dim,Batch,Data)
            y_target = yb
            y_pred = model(Input_tensor) #Forward
            #print(y_target.shape)
            #print(y_pred.shape)

        
            # initialize the gradient to zero
            optimizer_rnn.zero_grad()
            
            # compute and stock the loss
            loss = criterion(y_pred, y_target)

            # compute the gradient by back propagation
            loss.backward()

            optimizer_rnn.step()

            ls += (loss.item() / Input_tensor.shape[1])

        scheduler.step()
        # validate the model
        model.eval()
        # Check the performance on valiation data
        for xb, yb in validation_generator:
            Input_val = xb.unsqueeze(0)
            y_pred = model.predict(Input_val)
            y_target=yb
            vls = criterion(y_pred, y_target)
            valid_ls += (vls.item() / xb.shape[1])

        rmse = lambda x: round(sqrt(x * 1.000), 3)
        train_losses.append((rmse(ls)))
        valid_losses.append((rmse(valid_ls)))

        if epoch % 10 == 0:
            print('epoch: {} \ttraining Loss: {:.6f} \tvalidation Loss: {:.6f} \tBest Loss: {:.6f}'.format(epoch+1, train_losses[-1], valid_losses[-1],valid_loss_min))

        # save model if validation loss has decreased
        if valid_losses[-1] <= valid_loss_min:
            print('validation loss decreased ({:.6f} --> {:.6f}).  Saving model ...'.format(
            valid_loss_min,
            valid_losses[-1]))
            torch.save(model.state_dict(), model_name)
            valid_loss_min = valid_losses[-1]

    graph_loss(train_losses,valid_losses,"Lost",fig)

def Validation(model,validation_generator,code,id_CT,title,fig,CT_name):
    X_truth=[]
    X_pred=[]

    model.eval()
    for xb, yb in validation_generator:

        X,Y=Extract_Data_CT(code[id_CT],xb, yb)
        if X.shape[0] == 0 :
            continue
        
        Input_val = X.unsqueeze(0)

        if Input_val.ndim < 3 :
            continue
        # print(Input_val.shape)
        # print(Input_val.ndim)
        y_pred = model.predict(Input_val)
        y_target=Y
        # prediccion = sc.inverse_transform(y_pred)
        # #prediccion=y_pred
        # truth = sc.inverse_transform(y_target)
        X_truth.append(y_target)
        X_pred.append(y_pred)


    predi_final=[]
    target_final=[]

    for i in range(len(X_truth)):

        flat_list_truth = [item for sublist in X_truth[i] for item in sublist]
        flat_list_pred = [item for sublist in X_pred[i] for item in sublist]

        predi_final.append(flat_list_pred)
        target_final.append(flat_list_truth)


    predi_final= [item for sublist in predi_final for item in sublist]
    target_final= [item for sublist in target_final for item in sublist]
    title_pred = 'Mean Squared Error:' + CT_name
    print(title_pred, metrics.mean_squared_error(target_final, predi_final))
    graph_pred(target_final,predi_final,title,fig)
