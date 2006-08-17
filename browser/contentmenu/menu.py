from zope.interface import implements
from zope.component import getMultiAdapter

from zope.app.publisher.browser.menu import BrowserMenu
from zope.app.publisher.browser.menu import BrowserMenuItem
from zope.app.publisher.browser.menu import BrowserSubMenuItem

from Products.CMFCore.interfaces import IActionsTool
from Products.CMFCore.interfaces import IActionInfo

from Products.CMFCore.interfaces import IWorkflowTool
from Products.CMFCore.interfaces import IMembershipTool

from Products.CMFCore.utils import getToolByName

from Products.CMFDynamicViewFTI.interface import ISelectableBrowserDefault

from Products.CMFPlone.browser.interfaces import IPlone
from Products.CMFPlone.browser.plone import cache_decorator

from Products.CMFPlone.interfaces.structure import INonStructuralFolder
from Products.CMFPlone.interfaces.constrains import IConstrainTypes
from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes

from interfaces import IActionsSubMenuItem
from interfaces import IDisplaySubMenuItem
from interfaces import IFactoriesSubMenuItem
from interfaces import IWorkflowSubMenuItem

from interfaces import IActionsMenu
from interfaces import IDisplayMenu
from interfaces import IFactoriesMenu
from interfaces import IWorkflowMenu

from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone import utils

class ActionsSubMenuItem(BrowserSubMenuItem):
    implements(IActionsSubMenuItem)
    
    title = _(u'label_actions_menu', default=u'Actions')
    description = _(u'title_actions_menu', default=u'Actions for the current content item')
    submenuId = 'plone.contentmenu.actions.menu'
    
    order = 10
    extra = {'id' : 'plone.contentmenu.actions'}
    
    @property
    def action(self):
        parent = utils.parent(self.context)
        return parent.absolute_url() + '/folder_contents'
    
    @cache_decorator
    def available(self):
        _actionsTool = getToolByName(self.context, 'portal_actions')
        actionsTool = IActionsTool(_actionsTool)
        actions = actionsTool.listFilteredActionsFor(self.context)
        editActions = actions.get('object_buttons', None)        
        return (editActions is not None and len(editActions) >= 0)

    def selected(self):
        return False

class ActionsMenu(BrowserMenu):
    implements(IActionsMenu)
    
    def getMenuItems(self, context, request):
        """Return menu item entries in a TAL-friendly form."""
        results = []
        
        _actionsTool = getToolByName(context, 'portal_actions')
        actionsTool = IActionsTool(_actionsTool)
        
        actions = actionsTool.listFilteredActionsFor(context)
        editActions = actions.get('object_buttons', None)
        
        if editActions is None:
            return []
        
        plone_utils = getToolByName(context, 'plone_utils')
        
        for a in editActions:
            action = IActionInfo(a)
            if action['allowed']:
                icon = plone_utils.getIconFor('object_buttons', action['id'], None)
                cssClass = ''
                if icon:
                    cssClass = 'visualIconPadding visualIcon actionicon-object_buttons-%s' % action['id']
                    
                results.append({ 'title'        : action['title'],
                                 'description'  : '',
                                 'action'       : action['url'],
                                 'selected'     : False,
                                 'icon'         : icon,
                                 'extra'        : {'id' : action['id'], 'separator' : None, 'class' : cssClass},
                                 'submenu'      : None,
                                 })

        return results

class DisplaySubMenuItem(BrowserSubMenuItem):
    implements(IDisplaySubMenuItem)
    
    title = _(u'label_choose_template', default=u'Display')
    submenuId = 'plone.contentmenu.display.menu'
    
    order = 20
    
    @property
    def extra(self):
        return {'id' : 'plone.contentmenu.display', 'disabled' : self.disabled()}

    @property
    def description(self):
        if self.disabled():
            return _(u'title_remove_index_html_for_display_control', default=u'Delete or rename the index_html item to gain full control over how this folder is displayed.')
        else:
            return _(u'title_choose_default_view', default=u'Select the view mode for this folder, or set a content item as its default view.')
    
    @property
    def action(self):
        if self.disabled():
            return ''
        else:
            return self.context.absolute_url() + '/select_default_view'
    
    @cache_decorator
    def available(self):
        ploneView = getMultiAdapter((self.context, self.request), name="plone")
        isDefaultPage = ploneView.isDefaultPageInFolder()
        
        folder = None
        context = None
        
        folderLayouts = []
        contextLayouts = []
        
        # If this is a default page, also get menu items relative to the parent
        if isDefaultPage:
            folder = ISelectableBrowserDefault(utils.parent(self.context), None)
            
        context = ISelectableBrowserDefault(self.context, None)
        
        folderLayouts = []
        folderCanSetLayout = False
        folderCanSetDefaultPage = False
        
        if folder is not None:
            folderLayouts = folder.getAvailableLayouts()
            folderCanSetLayout = folder.canSetLayout()
            folderCanSetDefaultPage = folder.canSetDefaultPage()
            
        contextLayouts = []
        contextCanSetLayout = False
        contextCanSetDefaultPage = False
            
        if context is not None:
            contextLayouts = context.getAvailableLayouts()
            contextCanSetLayout = context.canSetLayout()
            contextCanSetDefaultPage = context.canSetDefaultPage()
        
        # Show the menu if we either can set a default-page, or we have more
        # than one layout to choose from.
        if (folderCanSetDefaultPage) or \
           (folderCanSetLayout and len(folderLayouts) > 1) or \
           (folder is None and contextCanSetDefaultPage) or \
           (contextCanSetLayout and len(contextLayouts) > 1):
            return True
        else:
            return False
        
    def selected(self):
        return False
        
    @cache_decorator
    def disabled(self):
        context = self.context
        ploneView = getMultiAdapter((self.context, self.request), name="plone")
        if ploneView.isDefaultPageInFolder():
            context = utils.parent(context)
        if not context.isPrincipiaFolderish:
            return False
        elif 'index_html' not in context.objectIds():
            return False
        else:
            return True
            

class DisplayMenu(BrowserMenu):
    implements(IDisplayMenu)
    
    def getMenuItems(self, obj, request):
        """Return menu item entries in a TAL-friendly form."""
        results = []

        ploneView = getMultiAdapter((obj, request), name="plone")
        isDefaultPage = ploneView.isDefaultPageInFolder()
        
        parent = None
        
        folder = None
        context = None
        
        folderLayouts = []
        contextLayouts = []
        
        # If this is a default page, also get menu items relative to the parent
        if isDefaultPage:
            parent = utils.parent(obj)
            folder = ISelectableBrowserDefault(parent, None)
            
        context = ISelectableBrowserDefault(obj, None)
        
        folderLayouts = []
        folderCanSetLayout = False
        folderCanSetDefaultPage = False
        
        if folder is not None:
            folderLayouts = folder.getAvailableLayouts()
            folderCanSetLayout = folder.canSetLayout()
            folderCanSetDefaultPage = folder.canSetDefaultPage()
            
        contextLayouts = []
        contextCanSetLayout = False
        contextCanSetDefaultPage = False
            
        if context is not None:
            contextLayouts = context.getAvailableLayouts()
            contextCanSetLayout = context.canSetLayout()
            contextCanSetDefaultPage = context.canSetDefaultPage()
        
        # Short circuit if neither folder nor object will provide us with
        # items
        if not (folderCanSetLayout or folderCanSetDefaultPage or \
                contextCanSetLayout or contextCanSetDefaultPage):
            return []
        
        # Only show the block "Folder display" and "Item display" separators if
        # they are necessars
        useSeparators = False
        if folderCanSetLayout or folderCanSetDefaultPage:
            if (contextCanSetLayout and len(contextLayouts) > 1) or contextCanSetDefaultPage:
                useSeparators = True
        
        # 1. If this is a default-page, first render folder options
        if folder is not None:
            folderUrl = parent.absolute_url()
            
            if useSeparators:
                results.append({ 'title'        : _(u'label_current_folder_views', default=u'Folder display'),
                                 'description'  : '',
                                 'action'       : None,
                                 'selected'     : False,
                                 'icon'         : None,
                                 'extra'        : {'id' : '_folderHeader', 'separator' : 'actionSeparator', 'class' : ''},
                                 'submenu'      : None,
                                 })
        
            if folderCanSetLayout:
                for id, title in folderLayouts:
                    results.append({ 'title'        : title,
                                     'description'  : '',
                                     'action'       : '%s/selectViewTemplate?templateId=%s' % (folderUrl, id,),
                                     'selected'     : False,
                                     'icon'         : None,
                                     'extra'        : {'id' : id, 'separator' : None, 'class' : ''},
                                     'submenu'      : None,
                                     })
            # Display the selected item (i.e. the context)
            results.append({ 'title'        : _(u'label_item_selected', default=u'Item: ${title}', mapping={'title' : context.Title()}),
                             'description'  : '',
                             'action'       : None,
                             'selected'     : True,
                             'icon'         : None,
                             'extra'        : {'id' : '_folderDefaultPageDisplay', 'separator' : 'actionSeparator', 'class' : ''},
                             'submenu'      : None,
                             })
            # Let the user change the selection
            if folderCanSetDefaultPage:
                results.append({ 'title'        : _(u'label_change_item', default=u'Change content item\nas default view...'),
                                 'description'  : _(u'title_change_default_view_item', default=u'Change the item used as default view in this folder'),
                                 'action'       : '%s/select_default_page' % (folderUrl,),
                                 'selected'     : False,
                                 'icon'         : None,
                                 'extra'        : {'id' : '_folderChangeDefaultPage', 'separator' : 'actionSeparator', 'class' : ''},
                                 'submenu'      : None,
                                 })
        
        # 2. Render context options
        if context is not None:
            contextUrl = obj.absolute_url()
            selected = context.getLayout()
            defaultPage = context.getDefaultPage()
            layouts = context.getAvailableLayouts()
            
            if useSeparators:
                results.append({ 'title'        : _(u'label_current_item_views', default=u'Item display'),
                                 'description'  : '',
                                 'action'       : None,
                                 'selected'     : False,
                                 'icon'         : None,
                                 'extra'        : {'id' : '_contextHeader', 'separator' : 'actionSeparator', 'class' : ''},
                                 'submenu'      : None,
                                 })
                                 
            # If context is a default-page in a folder, that folder's views will
            # be shown. Only show context views if there are any to show.
            
            showLayouts = False
            if not isDefaultPage:
                showLayouts = True
            elif len(layouts) > 1:
                showLayouts = True
            
            if showLayouts and contextCanSetLayout:
                for id, title in contextLayouts:
                    results.append({ 'title'        : title,
                                     'description'  : '',
                                     'action'       : '%s/selectViewTemplate?templateId=%s' % (contextUrl, id,),
                                     'selected'     : (defaultPage is None and id == selected),
                                     'icon'         : None,
                                     'extra'        : {'id' : id, 'separator' : None, 'class' : ''},
                                     'submenu'      : None,
                                     })
            
            # Allow setting / changing the default-page, unless this is a 
            # default-page in a parent folder.
            if not INonStructuralFolder.providedBy(obj):                   
                if defaultPage is None:
                    if contextCanSetDefaultPage:
                        results.append({ 'title'        : _(u'label_choose_item', default=u'Select a content item\nas default view...'),
                                         'description'  : _(u'title_select_default_view_item', default=u'Select an item to be used as default view in this folder...'),
                                         'action'       : '%s/select_default_page' % (contextUrl,),
                                         'selected'     : False,
                                         'icon'         : None,
                                         'extra'        : {'id' : '_contextSetDefaultPage', 'separator' : 'actionSeparator', 'class' : ''},
                                         'submenu'      : None,
                                         })                
            
                else:
                    results.append({ 'title'        : _(u'label_item_selected', default=u'Item: ${title}', mapping={'title' : context.Title()}),
                                     'description'  : '',
                                     'action'       : None,
                                     'selected'     : True,
                                     'icon'         : None,
                                     'extra'        : {'id' : '_contextDefaultPageDisplay', 'separator' : 'actionSeparator', 'class' : ''},
                                     'submenu'      : None,
                                     })
                    if contextCanSetDefaultPage:
                        results.append({ 'title'        : _(u'label_change_item', default=u'Change content item\nas default view...'),
                                         'description'  : _(u'title_change_default_view_item', default=u'Change the item used as default view in this folder'),
                                         'action'       : '%s/select_default_page' % (contextUrl,),
                                         'selected'     : False,
                                         'icon'         : None,
                                         'extra'        : {'id' : '_contextChangeDefaultPage', 'separator' : 'actionSeparator', 'class' : ''},
                                         'submenu'      : None,
                                         })
                             
        return results

class FactoriesSubMenuItem(BrowserSubMenuItem):
    implements(IFactoriesSubMenuItem)
    
    submenuId = 'plone.contentmenu.factories.menu'
    order = 30
    
    @property
    def extra(self):
        return {'id' : 'plone.contentmenu.factories', 
                'hideChildren' : self._hideChildren()}
    
    @property
    def title(self):
        addingToParent = self._addingToParent()
        itemsToAdd = self._itemsToAdd()
        showConstrainOptions = self._showConstrainOptions()
        if showConstrainOptions or len(itemsToAdd) > 1:
            if addingToParent:
                return _(u'label_add_new_item_in_folder', default=u'Add to folder')
            else:
                return _(u'label_add_new_item', default=u'Add item')
        elif len(itemsToAdd) == 1:
            itemTitle = itemsToAdd[0].Title()
            if addingToParent:
                return _(u'label_add_type_to_folder', default='Add ${type} to folder', mapping={'type' : itemTitle})
            else:
                return _(u'label_add_type', default='Add ${type}', mapping={'type' : itemTitle})
        else:
            return _(u'label_add_new_item', default=u'Add item')
    
    @property
    def description(self):
        addingToParent = self._addingToParent()
        itemsToAdd = self._itemsToAdd()
        showConstrainOptions = self._showConstrainOptions()
        if showConstrainOptions or len(itemsToAdd) > 1:
            if addingToParent:
                return _(u'title_add_new_items_inside_folder', default=u'Add new items in the same folder as this item')
            else:
                return _(u'title_add_new_items_inside_item', default=u'Add new items inside this item')
        elif len(itemsToAdd) == 1:
            return itemsToAdd[0].Description()
        else:
            return _(u'title_add_new_items_inside_item', default=u'Add new items inside this item')
    
    @property
    def action(self):
        if self._hideChildren():
            typeName = self._itemsToAdd()[0].getId()
            return self._addContext().absolute_url() + '/createObject?type_name=%s' % (typeName,)
        else:
            return self._addContext().absolute_url() + '/folder_factories'
    
    @property
    def icon(self):
        if self._hideChildren():
            fti = self._itemsToAdd()[0]
            return fti.getIcon()
        else:
            return None
    
    def available(self):
        itemsToAdd = self._itemsToAdd()
        showConstrainOptions = self._showConstrainOptions()
        return (len(itemsToAdd) > 0 or showConstrainOptions)

    def selected(self):
        return False
    
    @cache_decorator
    def _addContext(self):
        ploneView = getMultiAdapter((self.context, self.request), name="plone")
        return ploneView.getCurrentFolder()
        
    @cache_decorator
    def _itemsToAdd(self):
        addContext = self._addContext()
        constrain = IConstrainTypes(addContext, None)
        if constrain is None:
            return addContext.allowedContentTypes()
        else:
            locallyAllowed = constrain.getLocallyAllowedTypes()
            return [fti for fti in addContext.allowedContentTypes() if fti.getId() in locallyAllowed]
                
    @cache_decorator
    def _addingToParent(self):
        return (self._addContext().absolute_url() == self.context.absolute_url())
        
    @cache_decorator
    def _showConstrainOptions(self):
        addContext = self._addContext()
        constrain = ISelectableConstrainTypes(addContext, None)
        if constrain is None:
            return False
        elif constrain.canSetConstrainTypes():
            return True
        elif len(constrain.getLocallyAllowedTypes()) < len(constrain.getImmediatelyAddableTypes()):
            return True
            
    @cache_decorator
    def _hideChildren(self):
        itemsToAdd = self._itemsToAdd()
        showConstrainOptions = self._showConstrainOptions()
        return (len(itemsToAdd) == 1 and not showConstrainOptions)
            
class FactoriesMenu(BrowserMenu):    
    implements(IFactoriesMenu)
    
    def getMenuItems(self, context, request):
        """Return menu item entries in a TAL-friendly form."""
        results = []
        
        ploneView = getMultiAdapter((context, request), name="plone")
        addContext = ploneView.getCurrentFolder()
        
        allowedTypes = addContext.allowedContentTypes()
        
        # XXX: This is calling a pyscript (which we encourage people to 
        # customise TTW)
        exclude = addContext.getNotAddableTypes()
        include = None
        
        haveMore = False
        haveSettings = False
        
        constraints = IConstrainTypes(addContext, None)
        if constraints is not None:
            include = constraints.getImmediatelyAddableTypes()
            if len(include) < len(allowedTypes):
                haveMore = True

        constraints = ISelectableConstrainTypes(addContext, None)
        if constraints is not None:
            if constraints.canSetConstrainTypes():
                haveSettings = True

        for t in allowedTypes:
             typeId = t.getId()
             if typeId not in exclude and (include is None or typeId in include):
                 url = '%s/createObject?type_name=%s' % (addContext.absolute_url(), typeId,)
                 cssClass = 'visualIconPadding visualIcon contenttype-%s' % utils.normalizeString(typeId, context=context)
                 
                 results.append({ 'title'        : t.Title(),
                                  'description'  : t.Description(),
                                  'action'       : url,
                                  'selected'     : False,
                                  'icon'         : None,
                                  'extra'        : {'id' : typeId, 'separator' : None, 'class' : cssClass},
                                  'submenu'      : None,
                                 })

        if haveMore:
            url = '%s/folder_factories' % (addContext.absolute_url(),)
            results.append({ 'title'        : _(u'folder_add_more', default=u'More...'),
                             'description'  : _(u'Show all available content types'),
                             'action'       : url,
                             'selected'     : False,
                             'icon'         : None,
                             'extra'        : {'id' : '_more', 'separator' : None, 'class' : ''},
                             'submenu'      : None,
                            })

        if haveSettings:
            url = '%s/folder_constraintypes_form' % (addContext.absolute_url(),)
            results.append({'title'        : _(u'folder_add_settings', default=u'Restrict...'),
                            'description'  : _(u'title_configure_addable_content_types', default=u'Configure which content types can be added here'),
                            'action'       : url,
                            'selected'     : False,
                            'icon'         : None,
                            'extra'        : {'id' : '_settings', 'separator' : None, 'class' : ''},
                            'submenu'      : None,
                            })

        return results
        
class WorkflowSubMenuItem(BrowserSubMenuItem):
    implements(IWorkflowSubMenuItem)
    
    MANAGE_SETTINGS_PERMISSION = 'Manage portal'
    
    title = _(u'label_state', default=u'State:')
    submenuId = 'plone.contentmenu.workflow.menu'
    order = 40

    @property
    def extra(self):
        state = self._currentState()
        stateTitle = self._currentStateTitle()
        return {'id'         : 'plone.contentmenu.workflow', 
                'class'      : 'state-%s' % state,
                'state'      : state, 
                'stateTitle' : stateTitle,}
    
    @property
    def description(self):
        if self._manageSettings() or len(self._transitions()) > 0:
            return _(u'title_change_state_of_item', default=u'Change the state of this item')
        else:
            return u''

    @property
    def action(self):
        if self._manageSettings() or len(self._transitions()) > 0:
            return self.context.absolute_url() + '/content_status_history'
        else:
            return ''
    
    @cache_decorator
    def available(self):
        return (self._currentState() is not None)

    def selected(self):
        return False

    @cache_decorator
    def _manageSettings(self):
        _membershipTool = getToolByName(self.context, 'portal_membership')
        membershipTool = IMembershipTool(_membershipTool)
        return membershipTool.checkPermission(WorkflowSubMenuItem.MANAGE_SETTINGS_PERMISSION, self.context)

    @cache_decorator
    def _transitions(self):
        _actionsTool = getToolByName(self.context, 'portal_actions')
        actionsTool = IActionsTool(_actionsTool)
        actions = actionsTool.listFilteredActionsFor(self.context)
        workflowActions = actions.get('workflow', [])
        return workflowActions
        
    @cache_decorator
    def _currentState(self):
        _workflowTool = getToolByName(self.context, 'portal_workflow')
        workflowTool = IWorkflowTool(_workflowTool)
        return workflowTool.getInfoFor(self.context, 'review_state', default=None)        
        
    @cache_decorator
    def _currentStateTitle(self):
        _workflowTool = getToolByName(self.context, 'portal_workflow')
        workflowTool = IWorkflowTool(_workflowTool)
        state = workflowTool.getInfoFor(self.context, 'review_state', default=None)
        workflows = workflowTool.getWorkflowsFor(self.context)
        if workflows:
            for w in workflows:
                if w.states.has_key(state):
                    return w.states[state].title or state
    
class WorkflowMenu(BrowserMenu):
    implements(IWorkflowMenu)
    
    def getMenuItems(self, context, request):
        """Return menu item entries in a TAL-friendly form."""
        results = []
        
        _actionsTool = getToolByName(context, 'portal_actions')
        actionsTool = IActionsTool(_actionsTool)
        
        actions = actionsTool.listFilteredActionsFor(context)
        workflowActions = actions.get('workflow', None)

        if workflowActions is None:
            return []

        for a in workflowActions:
            action = IActionInfo(a)
            if action['allowed']:
                results.append({ 'title'        : action['title'],
                                 'description'  : '',
                                 'action'       : action['url'],
                                 'selected'     : False,
                                 'icon'         : None,
                                 'extra'        : {'id' : action['id'], 'separator' : None, 'class' : ''},
                                 'submenu'      : None,
                                 })

        url = context.absolute_url()

        if len(workflowActions) > 0:
            results.append({ 'title'         : _(u'label_advanced', default=u'Advanced...'),
                             'description'   : '',
                             'action'        : url + '/content_status_history',
                             'selected'      : False,
                             'icon'          : None,
                             'extra'         : {'id' : '_advanced', 'separator' : 'actionSeparator', 'class' : ''},
                             'submenu'       : None,
                            })
            results.append({ 'title'         : _(u'workflow_policy', default=u'Policy...'),
                             'description'   : '',
                             'action'        : url + '/placeful_workflow_configuration',
                             'selected'      : False,
                             'icon'          : None,
                             'extra'         : {'id' : '_policy', 'separator' : None, 'class' : ''},
                             'submenu'       : None,
                            })

        return results